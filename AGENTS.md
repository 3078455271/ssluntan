# AGENTS.md

本文件面向在本仓库工作的 AI 代理与新贡献者，说明项目结构、常用命令、约定与容易踩坑的地方。

## 项目概览

SSluntan 是一个前后端分离的论坛示例：

- **后端**：FastAPI + SQLAlchemy 2.0 异步 ORM + SQLite（可切 PostgreSQL）+ JWT。
- **前端**：Vue 3.5 + Vite + TypeScript + Pinia + Vue Router，纯手写 CSS，无 UI 组件库。
- **搜索**：`GET /api/search` 同时检索主题标题与全部楼层，前端 `/search` 页支持版块筛选、排序、分页和楼层深链。

`backend/app/web/` 是默认关闭的旧 Jinja 页面，除非任务明确要求，不要改动。

## 常用命令

### 后端（在 `backend/` 下执行）

```powershell
uv sync                              # 安装依赖
uv run uvicorn app.main:app --reload # 开发服务器，API 在 http://127.0.0.1:8000/api
uv run ruff check app tests          # 静态检查
uv run python -m pytest tests -q     # 测试（使用临时 SQLite，不写 forum.db）
uv run python -m scripts.promote_admin alice
```

在 Windows 上如 `uv run pytest` 报 `Failed to canonicalize script path`，改用 `uv run python -m pytest`；已存在的 `.venv` 也可直接执行 `.venv\Scripts\python.exe -m pytest tests -q`。

### 前端（在 `frontend/` 下执行）

```powershell
npm install
npm run dev        # http://127.0.0.1:5173，/api 代理到 :8000
npm run typecheck  # vue-tsc --noEmit
npm run build      # typecheck + vite build，产物在 dist/
```

提交前至少运行：`uv run ruff check app tests`、`uv run python -m pytest tests -q`、`npm run build`。

## 后端结构

```text
backend/app/
├── api/router.py          # 汇总所有路由，前缀来自 settings.api_prefix
├── api/routes/            # health/auth/users/boards/search/topics/posts
├── api/deps.py            # DbSession、当前用户等依赖
├── core/                  # config、database、security、errors
├── models/                # SQLAlchemy 模型（Board/Topic/Post/User）
├── schemas/               # Pydantic 请求 / 响应模型
├── services/              # 业务逻辑（forum、search、seed 等）
└── web/                   # 旧版 Jinja 页面，默认不挂载
```

分层约定：

- 路由只做参数校验、权限检查、调用 service、组装 `Page` 等响应。
- 查询与业务规则放在 `services/`，接收 `AsyncSession`，返回 ORM 对象或领域结果。
- 响应模型放在 `schemas/`，路由通过 `response_model` 声明。
- 异步全链路：`AsyncSession`、`await db.execute(...)`，不要引入同步 Session。
- 模型变更需要同时考虑 `alembic/versions/` 迁移；开发环境启动时也会 `create_all`，但这不能替代生产迁移。

## 前端结构

```text
frontend/src/
├── api/client.ts    # fetch 封装、token、ApiError、所有接口方法
├── api/types.ts     # 与后端响应对齐的 TypeScript 类型
├── components/      # AppHeader、TopicList、PaginationBar
├── router/index.ts  # 路由、登录/管理员守卫、401 处理
├── stores/          # Pinia：auth、notice
├── views/           # 页面级组件
├── utils/format.ts  # 日期、角色、首字母等格式化
├── App.vue          # 布局、全局提示、页面过渡
└── style.css        # 全站样式与 CSS 变量
```

约定：

- 页面使用 `<script setup lang="ts">`；导入顺序为 Vue/Router → `@/api` → `@/components` → `@/utils`，组内按字母序，组间空行。
- 使用 `@/` 别名，不写多级 `../../`。
- 所有界面文案使用简体中文。
- 新接口先在 `api/types.ts` 定义类型，再在 `api/client.ts` 增加方法，最后接入视图。
- 不引入 UI 框架或 CSS 框架；颜色、圆角、阴影使用 `style.css` 顶部的 CSS 变量。
- 动效必须尊重 `prefers-reduced-motion`，交互元素要有 `:focus-visible` 或清晰的 hover 反馈。
- 页面切换使用 `App.vue` 中基于 `route.path` 的 `<Transition name="page">`；同页 query 变化不会重挂载，需要 `watch` 路由 query。

## 搜索实现与深链约定

后端：

- 入口 `backend/app/api/routes/search.py`，服务 `backend/app/services/search.py`。
- 参数：`q`（去除首尾空白后至少 2 字）、`board_id`、`sort=relevance|latest`、`page`、`page_size`。
- 只搜索启用中的版块；标题命中优先，其次按最后活动时间；正文命中附带最早命中楼层与 120 字上下文。
- LIKE 查询对 `%`、`_`、`\` 做转义，用户输入按字面量匹配。
- 每个主题最多返回一条结果，正文命中的楼层通过一次批量查询取得，避免 N+1。
- 响应：`Page[SearchHit]`，`SearchHit = { topic: TopicRead, match: { matched_in, post_id, floor, snippet } }`。

前端：

- 搜索页 `views/SearchView.vue`，状态完全由 URL 驱动：`/search?q=&board=&sort=&page=`。
- 主题深链格式：`/topics/{id}?page={N}&post={postId}&floor={floor}`。
- 前端每页 `PAGE_SIZE = 20`，必须与后端默认 `page_size` 保持一致；`page = ceil(floor / 20)`。
- `TopicView.vue` 根据 `post` 参数高亮并滚动到目标楼层，楼层锚点为 `post-{post.id}`；找不到时显示提示，不阻塞页面。
- 修改分页大小、锚点规则或响应结构时，必须同步更新 `SearchView.vue`、`TopicView.vue` 与 `backend/tests/test_search.py`。

## 测试约定

- 后端测试位于 `backend/tests/`，`pytest-asyncio` 使用 `asyncio_mode = "auto"`。
- `conftest.py` 为每个测试创建临时 SQLite 引擎，并通过 `app.dependency_overrides[get_db]` 隔离真实数据库。
- 测试客户端用 `httpx.AsyncClient + ASGITransport`，不启动 lifespan，因此不会 seed 真实版块。
- 新增接口行为时优先写 API 级测试；涉及权限、过滤、分页、转义的行为必须有回归测试。
- 前端当前没有单测框架，依靠 `vue-tsc` 与 `vite build` 做静态校验；新增逻辑尽量保持纯函数、可复用。

## 注意事项

- 不要提交 `backend/forum.db`、`.env`、`frontend/dist`、`node_modules`。
- 后端命令默认在 `backend/` 工作目录执行，SQLite 相对路径依赖这一点。
- 生产环境必须替换 `SECRET_KEY`，并按需设置 `CORS_ORIGINS`。
- 管理端统计与版块列表使用 `include_inactive=true`，该参数仅管理员可用。
- 评估第三方 UI 组件（如 Vue Bits）时先阅读 `docs/vue-bits-evaluation.md`；当前项目不依赖 Tailwind，不要为了单个动效引入整套构建链。
