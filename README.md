# SSluntan

一个前后端分离的论坛示例：

- **后端**：FastAPI + 异步 SQLAlchemy 2.0 + SQLite（可切换 PostgreSQL）+ JWT 认证
- **前端**：Vue 3 + Vite + TypeScript + Pinia + Vue Router

```text
SSluntan/
├── backend/            # FastAPI 应用、数据库模型、业务逻辑
│   ├── app/
│   │   ├── api/        # JSON API 路由（前缀 /api）
│   │   ├── core/       # 配置、数据库、安全、错误
│   │   ├── models/     # SQLAlchemy ORM 模型
│   │   ├── schemas/    # Pydantic 请求 / 响应模型
│   │   ├── services/   # 论坛业务逻辑
│   │   └── web/        # 旧版 Jinja 页面（默认关闭）
│   ├── alembic/        # 迁移目录
│   ├── tests/          # pytest（临时 SQLite，不触碰 forum.db）
│   ├── scripts/        # 管理命令（如提升管理员）
│   ├── pyproject.toml
│   └── .env.example
├── frontend/           # Vue 3 单页应用
│   ├── src/api/        # API 客户端与 TypeScript 类型
│   ├── src/stores/     # Pinia 状态（登录态、全局提示）
│   ├── src/views/      # 首页 / 版块 / 主题 / 搜索 / 登录注册 / 个人中心 / 管理端
│   └── vite.config.ts  # 开发代理：/api → 127.0.0.1:8000
├── docs/               # 组件与 UX 评估文档
├── AGENTS.md           # 仓库协作约定（给 AI 代理 / 贡献者）
└── README.md
```

## 后端启动

需要 Python 3.12+ 和 [uv](https://docs.astral.sh/uv/)。

```powershell
cd backend
Copy-Item .env.example .env      # 按需修改 SECRET_KEY、数据库等
uv sync                          # 安装依赖（含 greenlet / async SQLAlchemy）
uv run uvicorn app.main:app --reload
```

启动后：

- API 根地址：<http://127.0.0.1:8000/api>
- 健康检查：<http://127.0.0.1:8000/api/health>
- Swagger 文档：<http://127.0.0.1:8000/docs>
- 首次启动会自动建表并写入 3 个默认版块（综合讨论 / 技术交流 / 站务反馈）

## 前端启动

需要 Node.js 20+。

```powershell
cd frontend
npm install
npm run dev
```

打开 <http://127.0.0.1:5173>。Vite 会把 `/api` 请求代理到 `http://127.0.0.1:8000`，开发时不需要额外处理跨域。

## 构建与校验

```powershell
# 前端类型检查 + 生产构建（产物在 frontend/dist）
cd frontend
npm run typecheck
npm run build

# 后端静态检查
cd ../backend
uv run ruff check app

# 后端测试（临时 SQLite，不写 forum.db）
uv run python -m pytest tests -q
```

生产部署时，前端构建为静态文件由 Nginx/CDN 托管；后端只提供 `/api`。若前后端不同源，在 `backend/.env` 中设置 `CORS_ORIGINS` 为前端域名（逗号分隔）。

## API 概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/register` | 注册（用户名、邮箱、密码） |
| POST | `/api/auth/login` | 登录，`application/x-www-form-urlencoded`，字段 `username`、`password` |
| GET | `/api/auth/me` | 当前登录用户 |
| GET / PATCH | `/api/users/me` | 查看 / 修改自己的资料 |
| GET | `/api/users/{username}` | 查看公开资料 |
| GET | `/api/boards` | 版块列表；`include_inactive=true` 仅管理员可用 |
| POST | `/api/boards` | 新建版块（管理员） |
| PATCH | `/api/boards/{board_id}` | 编辑、启用/停用版块（管理员） |
| GET | `/api/boards/id/{board_id}` / `/api/boards/{slug}` | 单个版块 |
| GET | `/api/topics` | 主题分页：`board_id`、`q`、`sort=latest\|hot\|new`、`page`、`page_size` |
| GET | `/api/search` | 全文搜索标题与全部楼层：`q`（≥2 字）、`board_id`、`sort=relevance\|latest`、`page`、`page_size` |
| POST | `/api/topics` | 发布主题（需登录） |
| GET / PATCH / DELETE | `/api/topics/{topic_id}` | 主题详情 / 编辑标题（作者）/ 置顶、锁定（管理员）/ 删除（作者、版主、管理员） |
| GET / POST | `/api/topics/{topic_id}/posts` | 楼层分页 / 回复主题（回复需登录） |
| PATCH / DELETE | `/api/posts/{post_id}` | 编辑 / 删除楼层（作者、版主、管理员；首帖不能单独删除） |
| GET | `/api/health` | 健康检查（含数据库探活） |

登录成功后后端返回 `access_token`，前端保存在 `localStorage`，后续请求自动附带 `Authorization: Bearer <token>`。

登录态处理：

- 同一浏览器的多个标签共享 token；任一标签登录、切换账号或退出后，其他标签通过 `storage` 事件同步 token 并重新请求 `/api/users/me`，避免用旧身份操作。
- 带 token 的请求返回 401 时会清除本地会话，并跳转登录页、通过 `redirect` 保留原页面。
- 任何 403 响应都会在页面顶部显示统一的无权限提示。
- 页面刷新时若本地 token 已失效，只静默清除会话，不会打断匿名浏览。

## 前端路由

| 路径 | 页面 |
| --- | --- |
| `/` | 首页：版块导航、搜索、主题排序与分页 |
| `/search` | 全文搜索：关键词、版块、排序、分页，结果可直达命中楼层 |
| `/boards/:slug` | 版块主题列表 |
| `/topics/:id` | 主题详情：楼层、分页、回复、作者/版主删除 |
| `/topics/new` | 发布主题（需登录） |
| `/login`、`/register` | 登录 / 注册 |
| `/profile` | 个人中心：头像、简介、退出登录（需登录） |
| `/admin` | 管理端：版块增改启停、主题置顶/锁定/删除（需管理员） |
| `/403` | 无权限提示页 |

## 站内搜索

`GET /api/search` 同时检索主题标题和全部楼层，只返回启用版块中的主题：

- 关键词去除首尾空白后至少 2 个字符；`%`、`_` 按字面量匹配。
- 默认按「标题命中优先，其次最后活动时间」排序，`sort=latest` 则只按最后活动时间。
- 正文命中的结果返回最早命中的楼层、楼层 ID 和约 120 字上下文片段。
- 前端结果链接形如 `/topics/{id}?page={N}&post={postId}&floor={floor}`，主题页会高亮并滚动到对应楼层；目标已被删除时显示提示。
- 分页大小 20 必须与前端 `SearchView.vue` 的 `PAGE_SIZE` 保持一致。

前端动效与 Vue Bits 的选型评估见 [docs/vue-bits-evaluation.md](docs/vue-bits-evaluation.md)。

## 管理端

注册用户默认是 `member`。先手动把已有账号提升为管理员：

```powershell
cd backend
uv run python -m scripts.promote_admin alice
```

刷新页面或重新登录后，顶部导航会出现「管理」入口，访问 <http://127.0.0.1:5173/admin> 即可：

- 版块管理：新建、编辑、启用/停用版块，查看已停用版块。
- 主题管理：按版块、排序和分页浏览，置顶/取消置顶、锁定/解锁、删除主题。
- 楼层管理：主题页中作者、版主和管理员可删除非首帖楼层。

`/admin` 路由会同时校验登录状态和 `admin` 角色；普通成员访问会进入 `/403`。管理端列出已停用版块依赖 `GET /api/boards?include_inactive=true`，该参数现在仅对管理员开放，匿名或普通成员请求返回 403。

当前管理端与前台共用同一 SPA/origin（`/admin`），部署最简单；JWT 仍属于同一 origin 的会话。若之后需要更严格的 origin 隔离，可以再拆分独立管理端，并把新域名加入 `CORS_ORIGINS`。

## 关于旧版 Jinja 页面

`backend/app/web/` 仍保留原来的服务端渲染页面（Cookie 会话 + CSRF）。前后端分离模式下默认不挂载（`ENABLE_LEGACY_WEB_UI=false`）。如需兼容旧页面，把它设为 `true` 后重启即可。

## 配置项

主要环境变量见 `backend/.env.example`：

- `API_PREFIX`：API 前缀，默认 `/api`
- `ENABLE_LEGACY_WEB_UI`：是否挂载旧 Jinja 页面，默认 `false`
- `SECRET_KEY`：JWT 签名密钥，部署前务必替换
- `DATABASE_URL`：默认 `sqlite+aiosqlite:///./forum.db`（相对于 `backend/` 运行目录）
- `AUTO_CREATE_TABLES` / `SEED_DEFAULT_DATA`：启动时建表 / 写入默认版块
- `CORS_ORIGINS`：允许的前端来源，逗号分隔
- 前端可用 `VITE_API_BASE` 覆盖 API 根地址（默认 `/api`，配合 Vite 代理）

