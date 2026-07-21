# kimi-code改色插件

**kimi-cli-visual** · v1.0.0

kimi-code CLI（v0.28.1）的终端界面美化组件：将「紫金玫」配色与 Golden Night 字符流光（斜向扫光动画）注入 TUI 的启动横幅、信息面板、提示横幅与底栏模型名，并附带一套兼容官方自定义主题机制的主题文件。全部改动脚本化、锚定唯一、幂等可重跑。

![kimi-cli-visual 演示](https://raw.githubusercontent.com/shanghua1/kimi-cli-visual/f55d325ec98746563fe5e6ea491bcfaeca56933f/docs/assets/kimi-cli-visual.gif)

## 效果一览

- 启动横幅整板流光：方块 logo 七阶渐变（深紫 → 亮紫 → 金 → 堇）、Welcome 标题、帮助行
- Directory / Session / Model / Version 信息行斜向扫光，行间 +1 相位形成对角推进
- ✦ 提示横幅（远程 tips 动态文案）逐帧上色，文案更新不影响效果
- 底栏模型名常驻流光；`/dance on` / `/dance off` 随时开关
- 30 FPS（帧表 110ms → 33ms）；同一视觉行的多段文字共享坐标系，光带连续无断层
- 只改前景色与字重：空白严格遮罩，不动文字内容、坐标与布局

## 配色主题

流光调色板（banner 底色波，8 色循环）：

| #8A6FC0 | #9D8BD4 | #FF8799 | #CD96CD | #EAC364 | #CD96CD | #FF8799 | #9D8BD4 |
|---|---|---|---|---|---|---|---|
| 紫 | 堇 | 玫瑰粉 | 主紫 | 金（峰） | 主紫 | 玫瑰粉 | 堇 |

logo 专属七阶渐变（7 格一格一色，亮度递升至金峰后回落）：

`#473C8B → #6A58A6 → #9D8BD4 → #CD96CD → #EAC364 → #B7A6E8 → #8A6FC0`

高光与扫光参数（见 `palette.json`）：香槟金高光（core `#FFE9B3` / shoulder `#EAC364`）；光带核心 0.035、肩光 0.105、前导 0.19、拖尾 0.34；speed 1.2、strength 1.0。

界面主题：`themes/zijin.json`（19 个官方主题 token，暗色基底的紫金配色）。

## 实现原理

1. **结构解析**：kimi.exe 是 Node.js SEA（Single Executable Application），内嵌一份未压缩、未混淆的 rolldown JS bundle（约 16 MB 明文，函数名与源码路径俱全），存放于 `.rsrc` 节的 `NODE_SEA_BLOB` 资源中。blob 头部含 `code_len` 字段，尾部为 web assets 与 sha256 清单；运行时不自验 JS 代码区。
2. **补丁管线**（`extract → palette → shimmerize → rebuild → inject`，均幂等）：
   - 解析 PE 资源目录定位 blob，拆出 99 字节头 / main.cjs / 尾部数据；
   - 以**唯一字符串锚定**替换 9 处：`DARK_RAINBOW` 调色板 8 色等长替换；`rainbowText` 函数体替换为流光实现（斜向光带采样 + 高斯字重悦动 + 共享坐标系 + CJK 宽字符处理）；`RainbowDance` 帧表提速与永续化、常驻自启；welcome / banner 组件渲染点接线（信息行原文、帮助行、tips 主副文）；
   - 重建 blob（仅改 `code_len`），用 postject 重建 PE 资源目录注入（实测 `.rsrc` 尾部空闲仅约 1.8 KB，扩容必须重建资源目录而非就地写字节）。
3. **验证链**：19 项单元测试（字符守恒 / 光带移动 / 增亮 / 空白遮罩 / 确定性 / CJK / 采样数值 / 同行跨段一致 / 渐变单调性）→ `node --check` → bundle 直跑 `--version` → 注入后 `--version` 与 `doctor` → 真实终端冒烟。任何锚定命中数不等于 1 时脚本拒绝补丁（对官方升级后的偏移漂移安全失败）。
4. **界面主题**走官方自定义主题机制（`~/.kimi-code/themes/*.json`），不属于二进制补丁。

## 文件结构

| 文件 | 说明 |
|---|---|
| `extract_blob.py` | 从 kimi.exe 解析并提取 SEA blob（头 / 代码 / 尾部） |
| `patch_palette.py` | DARK_RAINBOW 8 色等长替换为紫金玫波浪 |
| `shimmerize.py` | 流光核心注入（9 处锚定编辑 + 命中报告） |
| `rebuild_blob.py` | 以新代码重建 blob（更新 code_len） |
| `inject_exe.py` | postject 注入并三重自验（资源大小 / 头长度 / 逐字节一致） |
| `sea_pe.py` | 共享库：PE/.rsrc 解析与 blob 头读写 |
| `test_shimmer.js` | 19 项单元测试（node test_shimmer.js） |
| `palette.json` | 流光配色主题存档（调色板 / 渐变 / 高光 / 扫光参数） |
| `themes/zijin.json` | 官方自定义主题文件（紫金配色，19 token） |

## 使用方法

环境：Windows、Node.js ≥ 20、Python ≥ 3.10。

```bash
npm install                 # 安装 postject
python extract_blob.py <干净 kimi.exe 路径>
python patch_palette.py
python shimmerize.py
node test_shimmer.js        # 19/19 应全过
python rebuild_blob.py build/main.final.cjs build/blob.final.bin
python inject_exe.py build/blob.final.bin build/kimi.final.exe
# 校验 kimi.final.exe --version 与 doctor 通过后，备份原 exe 再替换
```

主题安装：复制 `themes/zijin.json` 到 `~/.kimi-code/themes/`，在 `tui.toml` 设 `theme = "zijin"`。

## 注意事项

- 补丁会使 Authenticode 签名失效（不影响本机运行）。
- 官方升级会覆盖补丁：建议在 `tui.toml` 设 `[upgrade] auto_install = false`；升级后可对新版本重跑本管线。
- 锚定字符串针对 v0.28.1 实测；若版本变化导致锚定漂移，脚本会因命中数 ≠ 1 而拒绝执行（安全失败）。
- 操作前请备份 `kimi.exe`。
- 本项目为第三方美化补丁，与 kimi-code 官方无关。请在自有授权的 kimi-code 副本上执行补丁；本仓库不含、也不应再分发官方二进制。

## 许可证与第三方声明

本项目原创脚本采用 MIT License，详见 [`LICENSE`](LICENSE)。其中改编自 Kimi Code v0.28.1 的代码片段及 npm 依赖的来源与许可证，详见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。Kimi 与 Kimi Code 为 Moonshot AI 的产品名称；本项目与 Moonshot AI 无隶属或授权关系。

## 版本

**1.0.0**（2026-07-22）：首个公开发布。
