# Vue Bits 评估与 UX 落地方案

> 结论：**当前阶段不引入 Vue Bits**。本次搜索页所需的层次感、结果入场、悬停反馈和楼层高亮，已经用原生 CSS 实现（见 `frontend/src/style.css` 末尾与 `App.vue` 页面过渡）。如果后续确实要采用，建议只挑选 1 个组件、以源码 vendoring 方式引入，并先通过下述许可证与依赖审查。

## 1. 项目事实

- 官方仓库：[DavidHDev/vue-bits](https://github.com/DavidHDev/vue-bits)，是 React Bits 的官方 Vue 移植版。
- 提供 90+ 个动画/文本/背景组件，通过 [jsrepo](https://jsrepo.dev) CLI（或其 shadcn 风格流程）把组件源码复制到项目，而不是安装一个运行时包。
- Vue Bits 仓库自身使用 Vue 3.5、Vite 7、Tailwind CSS 4；示例组件普遍以 Tailwind utility class 书写，部分组件还依赖 `motion-v`、`gsap`、`three`、`ogl`、`@vueuse/core` 等，按组件按需引入。
- 本项目当前是 Vue 3.5 + Vite 8，**没有 Tailwind**，样式集中在 `frontend/src/style.css` 的 CSS 变量与手写 class 上。

## 2. 许可证

Vue Bits 使用 **MIT + Commons Clause License Condition v1.0**（版权方 David Haz，2025）：

- 允许商业使用，也允许把组件作为应用、网站或产品的一部分使用、修改和分发。
- **不允许**单独销售、再许可或重新分发组件本身，也不允许把它们打包成 bundle、模板或“移植版”出售。
- 分发时需要保留版权与许可声明。

对本项目的含义：论坛本身可以商用；但不能把引入的组件再包装成组件库/模板售卖。复制源码时应保留声明，具体法律问题请以仓库 `LICENSE.md` 为准。

## 3. 适配度评估

| 候选组件 | 可用场景 | 成本 / 风险 | 结论 |
| --- | --- | --- | --- |
| Text Animator | 搜索页大标题逐字入场 | 需要 Tailwind 或改写 class；可能引入 `motion-v`/`gsap`；标题动画过度会干扰阅读 | 暂缓，现有 CSS 标题 + 页面过渡已足够 |
| Animated Content | 搜索结果滚动入场 | 每张卡片一个观察器；项目已用 `row-rise` + `animationDelay` 实现 | 不采用 |
| Aurora / Gradient / Particles 背景 | 搜索 hero 装饰背景 | Canvas/WebGL 成本高，移动端耗电，低端设备掉帧，且需额外无障碍降级 | 不采用，现有 radial-gradient 已覆盖 |
| Spotlight Card | 主题卡片鼠标跟随光斑 | 需要逐卡 JS 指针监听与 Tailwind；触屏无收益 | 可延后，优先做 CSS-only fallback |
| Count Up | 统计数字动画 | 论坛目前没有需要强调的数字指标 | 不采用 |
| Stepper / Scroll Stack 等 | 与论坛信息架构不匹配 | 改造成本高 | 不采用 |

## 4. 如果后续采用：约束条件

1. **源码 vendoring**：只把选中的单个组件复制到 `frontend/src/components/vue-bits/`，不新增全量依赖或全局 Tailwind 构建链。
2. **样式隔离**：把组件里的 Tailwind utility 转换为项目 CSS 变量/scoped CSS；或仅在该组件目录内启用最小 Tailwind 配置，避免 preflight 影响现有页面。
3. **按需依赖**：确认该组件实际需要 `motion-v`、`gsap` 或 `three` 中的哪一个，能改用 CSS/Web Animations API 就改；禁止为一个 hover 效果引入 3D 引擎。
4. **性能与无障碍**：所有动画支持 `prefers-reduced-motion: reduce`；首屏外动画使用 `IntersectionObserver`；Canvas/WebGL 组件必须提供静态降级。
5. **许可证留存**：在组件目录放 `LICENSE.vue-bits.md` 或等效声明，记录来源、版本与修改。
6. **验收标准**：Lighthouse 性能与可访问性不下降、`npm run build` 通过、移动端 60fps 无明显掉帧，否则回退。

## 5. 本次已落地的替代方案

不引入依赖也完成了同类 UX 目标：

- **页面切换**：`App.vue` 中 `<Transition name="page" mode="out-in">` + `route.path` key，淡入并轻微上移。
- **搜索结果**：`SearchView.vue` 对每张结果设置 `animationDelay`，`style.css` 的 `row-rise` 负责入场；hover 时卡片抬升、箭头右移。
- **列表节奏**：`TopicList.vue` 按行设置 30ms 递增延迟。
- **深链定位**：正文命中打开 `/topics/{id}?page=&post=&floor=`，`TopicView.vue` 用 `post-target` 高亮目标楼层并平滑滚动。
- **降级**：以上动效在 `prefers-reduced-motion: reduce` 下全部关闭。

## 6. 建议的下一步 UX 方向（不依赖 Vue Bits）

1. 搜索页增加“最近搜索”与空结果建议词，减少重复输入。
2. 为正文命中显示命中位置附近的楼层导航（上一楼 / 下一楼），复用现有 `post` 深链。
3. 给搜索结果增加“仅标题 / 仅正文”筛选，后端在现有 `matched_in` 基础上扩展即可。
4. 用 CSS `scroll-snap` 或 `view-transition-name` 改善楼层定位，而不是引入动画库。
