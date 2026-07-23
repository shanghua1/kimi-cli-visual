# kimi-cli-visual · Golden Night 字符流光

> 终端字符流光效果：静态「紫金玫」色板为底，一道香槟金光带斜向扫过文字——白芯、金肩、玫尾，30 FPS。
> 本仓库收录流光算法本体（零依赖 JS 模块）、可直接运行的终端演示、单元测试与配色主题存档。

![kimi-cli-visual 演示](docs/assets/kimi-cli-visual.gif)

## 本地体验

```bash
node demo.js            # 在终端里直接观看流光动画（Ctrl+C 退出）
node demo.js --frames 3 # 冒烟模式：打印 3 帧后退出
node test_shimmer.js    # 29 项单元测试
```

需要支持 24-bit 真彩的终端（Windows Terminal / WezTerm / iTerm2 等）；Node.js ≥ 18，无任何依赖。

## 算法要点（`shimmer-core.js`）

- **斜向光带采样** `shimmerSample(projection, time, symmetric, widths)`：光带分四区——核心（强度 1）、肩光（0.26→0.74 线性）、拖尾（二次衰减）、前导微光；`symmetric=true` 时前缘镜像后缘成对称光带，`widths` 可收窄成一道细颙。
- **共享坐标系**：同一视觉行的多段文字各自传 `xOffset / totalWidth`，光带跨段连续无断层（单测逐位校验）。
- **CJK 感知**：宽字符按 2 格计入光带投影，中英文混排光速一致。
- **高光可定制**：`highlight` 参数覆盖三区颜色（core / shoulder / trail）与 `strength / cap / boldFloor`；把三色反转为暗色即得「隐没暗带」——亮底终端上暗影比白闪更醒目。
- **字重悦动**：高斯权重（σ≈0.112）随光带经过放宽加粗阈值，光峰邻域文字微微变粗。
- **严格无损**：只改前景色与字重；空格不上色，字符内容、坐标与布局分毫不动。

## 配色

流光基色波（8 色循环，金为峰）：

| #8A6FC0 | #9D8BD4 | #FF8799 | #CD96CD | #EAC364 | #CD96CD | #FF8799 | #9D8BD4 |
|---|---|---|---|---|---|---|---|
| 紫 | 堇 | 玫瑰粉 | 主紫 | 金（峰）标 | 主紫 | 玫瑰粉 | 堇 |

logo 专属七阶渐变（一格一色，亮度递升至金峰后回落）：

`#473C8B → #6A58A6 → #9D8BD4 → #CD96CD → #EAC364 → #B7A6E8 → #8A6FC0`

配色哲学：紫为体、金为饰、银白为光（<5% 面积，仅光峰）。全部参数存档见 [`palette.json`](palette.json)。

`themes/zijin.json` 是配套的「星夜紫金」暗色界面主题（19 个通用 token），可用于任何支持 JSON 主题定义的终端应用。

## 说明

- 演示 GIF 录制于作者本机的终端实验环境。本仓库仅包含原创的流光算法、演示脚本与主题文件，**不含任何第三方应用的代码、二进制或修改工具**。
- Kimi 与 Kimi Code 是 Moonshot AI 的产品名称；本项目为个人视觉实验，与 Moonshot AI 无障属或授权关系。

## 许可证

MIT，详见 [`LICENSE`](LICENSE)。

## 版本

- **2.0.0**（2026-07-23）：重构为纯算法仓库——收录 `shimmer-core.js`（对称光带 / 窄带 / 隐没暗带 / 高光参数化）、终端演示 `demo.js` 与 29 项单测；移除全部与第三方程序相关的工具脚本。
- 1.0.0（2026-07-22）：首个公开发布。
