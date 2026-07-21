# -*- coding: utf-8 -*-
"""Golden Night 字符流光注入脚本：把斜向扫光核心内联进 kimi-code 内嵌 bundle（以 /dance 彩蛋为宿主）。

特性：
  * 同步：banner 同一行的 logo 与文字共享相位与连续 x 坐标（光带从 logo 无缝流入文字）
  * 帧率：RainbowDance 帧表 110ms → 33ms（≈30 FPS；SHIMMER_FRAME_MS 同步）
  * 覆盖：welcome 标题/帮助行/信息行、tips 横幅（✦ 主文+副文）、footer 模型名；每行 +1 相位形成斜向光带
  * logo 专属七阶紫金渐变（不染玫粉）；全局香槟金高光

锚定编辑 9 处（每处必须全文件唯一，否则拒绝）：
  E1 rainbowText → shimmer 核心（新增 xOffset/totalWidth 参，签名向后兼容）
  E2 settle(hold) 永续
  E3 installRainbowDance 常驻自启
  E4 renderDanceWelcomeHeader 同行同相+连续x（新增 rightRow1Text 参）
  E5 RainbowDance 帧表 110→33
  E6 welcome.ts 抽出 rightRow1Text 原文
  E7 welcome.ts 调用点传 rightRow1Text
  E8 welcome.ts infoRaw + contentLines 起舞时整板流光
  E9 banner.ts tips 主/副文起舞时流光

用法: python shimmerize.py [in.cjs] [out.cjs]
默认: build/main.palette.cjs -> build/main.final.cjs
幂等: 已含 SHIMMER 标记则报告并原样写出。另产出 build/dance-snippet.js 供单测。"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'build', 'main.palette.cjs')
DST = os.path.join(HERE, 'build', 'main.final.cjs')
SNIPPET = os.path.join(HERE, 'build', 'dance-snippet.js')

# ---------- E1：rainbowText → 真 shimmer（v2：共享坐标系） ----------
OLD1 = (
    '/** Paint a string character-by-character through a palette, skipping spaces. */\n'
    'function rainbowText(text, colors, offset = 0, bold = false) {\n'
    '\tlet colorIndex = offset;\n'
    '\treturn Array.from(text).map((char) => {\n'
    '\t\tif (char === " ") return char;\n'
    '\t\tconst color = colors[colorIndex % colors.length] ?? colors[0];\n'
    '\t\tcolorIndex++;\n'
    '\t\tconst style = chalk.hex(color);\n'
    '\t\treturn bold ? style.bold(char) : style(char);\n'
    '\t}).join("");\n'
    '}'
)
NEW1 = (
    '/** Golden Night shimmer core, ported from text-shimmer.js (ncm-visual-lab). */\n'
    'const SHIMMER_CORE_RGB = [255, 233, 179];\n'
    'const SHIMMER_SHOULDER_RGB = [234, 195, 100];\n'
    'const SHIMMER_CYCLE_SPAN = 1.72;\n'
    'const SHIMMER_RATE = 0.34;\n'
    'const SHIMMER_SPEED = 1.2;\n'
    'const SHIMMER_STRENGTH = 1;\n'
    'const SHIMMER_FRAME_MS = 33;\n'
    'const SHIMMER_LOGO_PALETTE = ["#473C8B", "#6A58A6", "#9D8BD4", "#CD96CD", "#EAC364", "#B7A6E8", "#8A6FC0"];\n'
    'function shimmerParseHex(hex) {\n'
    '\tconst n = Number.parseInt(String(hex).replace("#", ""), 16);\n'
    '\treturn [(n >> 16) & 255, (n >> 8) & 255, n & 255];\n'
    '}\n'
    'function shimmerToHex(rgb) {\n'
    '\treturn "#" + rgb.map((c) => Math.max(0, Math.min(255, Math.round(c))).toString(16).padStart(2, "0")).join("");\n'
    '}\n'
    'function shimmerMix(from, to, amount) {\n'
    '\tconst r = Math.max(0, Math.min(1, amount));\n'
    '\treturn from.map((c, i) => c + (to[i] - c) * r);\n'
    '}\n'
    'function shimmerCharWidth(char) {\n'
    '\tconst code = char.codePointAt(0);\n'
    '\tif (code <= 31 || (code >= 127 && code <= 159)) return 0;\n'
    '\tif (code >= 4352 && (code <= 4447 || code === 9001 || code === 9002 || (code >= 11904 && code <= 42191 && code !== 12351) || (code >= 44032 && code <= 55203) || (code >= 63744 && code <= 64255) || (code >= 65040 && code <= 65049) || (code >= 65072 && code <= 65135) || (code >= 65280 && code <= 65376) || (code >= 65504 && code <= 65510) || (code >= 127744 && code <= 129535))) return 2;\n'
    '\treturn 1;\n'
    '}\n'
    '/** Diagonal sweep intensity at a normalized position. Direct port of sampleDiagonalSweep(). */\n'
    'function shimmerSample(projection, time) {\n'
    '\tconst head = ((time * SHIMMER_SPEED * SHIMMER_RATE) % SHIMMER_CYCLE_SPAN + SHIMMER_CYCLE_SPAN) % SHIMMER_CYCLE_SPAN - 0.24;\n'
    '\tconst distance = projection - head;\n'
    '\tconst ad = Math.abs(distance);\n'
    '\tif (ad <= 0.035) return { intensity: 1, core: true, distance };\n'
    '\tif (ad <= 0.105) {\n'
    '\t\tconst shoulder = 1 - (ad - 0.035) / 0.07;\n'
    '\t\treturn { intensity: 0.26 + shoulder * 0.48, core: false, distance };\n'
    '\t}\n'
    '\tif (distance > 0.105 && distance <= 0.34) {\n'
    '\t\tconst trail = 1 - (distance - 0.105) / 0.235;\n'
    '\t\treturn { intensity: 0.26 * trail * trail, core: false, distance };\n'
    '\t}\n'
    '\tif (distance < -0.105 && ad <= 0.19) {\n'
    '\t\tconst lead = 1 - (ad - 0.105) / 0.085;\n'
    '\t\treturn { intensity: 0.14 * lead * lead, core: false, distance };\n'
    '\t}\n'
    '\treturn { intensity: 0, core: false, distance };\n'
    '}\n'
    '/** Paint a string with the Golden Night sweep: static palette base, silver band gliding over it.\n'
    '* xOffset/totalWidth let multiple segments of one visual row share a single coordinate system. */\n'
    'function rainbowText(text, colors, offset = 0, bold = false, xOffset = 0, totalWidth = 0, highlight) {\n'
    '\tconst highlightCore = highlight?.core ?? SHIMMER_CORE_RGB;\n'
    '\tconst highlightShoulder = highlight?.shoulder ?? SHIMMER_SHOULDER_RGB;\n'
    '\tconst chars = Array.from(text);\n'
    '\tconst columns = [];\n'
    '\tlet totalCells = 0;\n'
    '\tfor (const char of chars) {\n'
    '\t\tcolumns.push(totalCells);\n'
    '\t\ttotalCells += Math.max(1, shimmerCharWidth(char));\n'
    '\t}\n'
    '\tconst span = Math.max(totalWidth, xOffset + totalCells);\n'
    '\tconst time = offset * SHIMMER_FRAME_MS / 1000;\n'
    '\tlet colorIndex = 0;\n'
    '\treturn chars.map((char, index) => {\n'
    '\t\tif (char === " ") return char;\n'
    '\t\tconst base = shimmerParseHex(colors[colorIndex % colors.length] ?? colors[0]);\n'
    '\t\tcolorIndex++;\n'
    '\t\tconst projection = span <= 1 ? 0 : (xOffset + columns[index]) / (span - 1) * 0.72;\n'
    '\t\tconst sample = shimmerSample(projection, time);\n'
    '\t\tif (sample.intensity <= 0.006) {\n'
    '\t\t\tconst style = chalk.hex(shimmerToHex(base));\n'
    '\t\t\treturn bold ? style.bold(char) : style(char);\n'
    '\t\t}\n'
    '\t\tconst coreColor = shimmerMix(highlightShoulder, highlightCore, sample.core ? 0.86 : 0.28);\n'
    '\t\tconst amount = Math.min(0.72, sample.intensity * (sample.core ? 0.62 : 0.3) * SHIMMER_STRENGTH);\n'
    '\t\tconst weight = Math.exp(-Math.pow(sample.distance / 0.112, 2));\n'
    '\t\tconst style = chalk.hex(shimmerToHex(shimmerMix(base, coreColor, amount)));\n'
    '\t\treturn bold || sample.core || weight > 0.24 ? style.bold(char) : style(char);\n'
    '\t}).join("");\n'
    '}\n'
    '/** Shimmer one banner line with the shared dance phase; rowLag tilts the sweep diagonally. */\n'
    'function shimmerBannerLine(text, rowLag, bold, totalWidth) {\n'
    '\tconst palette = getDanceRainbowPalette();\n'
    '\tconst phase = (currentDanceView?.phase ?? 0) + rowLag;\n'
    '\treturn rainbowText(text, palette, phase, bold, 0, totalWidth);\n'
    '}'
)

# ---------- E2：settle(hold) 永续 ----------
OLD2 = (
    '\t\tsettle(hold) {\n'
    '\t\t\tthis.clearTimers();\n'
    '\t\t\tif (!hold) {\n'
    '\t\t\t\tthis.isColored = false;\n'
    '\t\t\t\tthis.currentPhase = 0;\n'
    '\t\t\t}\n'
    '\t\t\tthis.requestRender();\n'
    '\t\t}'
)
NEW2 = (
    '\t\tsettle(hold) {\n'
    '\t\t\tif (hold) {\n'
    '\t\t\t\tif (this.flowStopTimer !== null) {\n'
    '\t\t\t\t\tclearTimeout(this.flowStopTimer);\n'
    '\t\t\t\t\tthis.flowStopTimer = null;\n'
    '\t\t\t\t}\n'
    '\t\t\t} else {\n'
    '\t\t\t\tthis.clearTimers();\n'
    '\t\t\t\tthis.isColored = false;\n'
    '\t\t\t\tthis.currentPhase = 0;\n'
    '\t\t\t}\n'
    '\t\t\tthis.requestRender();\n'
    '\t\t}'
)

# ---------- E3：常驻自动起舞 ----------
OLD3 = (
    'function installRainbowDance(requestRender) {\n'
    '\tcurrentDanceController?.dispose();\n'
    '\tconst dance = new RainbowDance(requestRender);\n'
    '\tsetRainbowDance(dance);\n'
    '\treturn () => {'
)
NEW3 = (
    'function installRainbowDance(requestRender) {\n'
    '\tcurrentDanceController?.dispose();\n'
    '\tconst dance = new RainbowDance(requestRender);\n'
    '\tsetRainbowDance(dance);\n'
    '\tdance.start({ hold: true });\n'
    '\treturn () => {'
)

# ---------- E4：renderDanceWelcomeHeader 同行同相+连续 x ----------
OLD4 = (
    'function renderDanceWelcomeHeader(logo, textWidth, rightRow1) {\n'
    '\tconst phase = currentDanceView?.phase ?? 0;\n'
    '\tconst palette = getDanceRainbowPalette();\n'
    '\tconst logoWidth = Math.max(...logo.map((row) => visibleWidth(row)));\n'
    '\tconst gap = "  ";\n'
    '\tconst rightRow0 = truncateToWidth(rainbowText("Welcome to Kimi Code!", palette, phase + 2, true), textWidth, "…");\n'
    '\treturn [rainbowText(logo[0].padEnd(logoWidth), palette, phase) + gap + rightRow0, rainbowText(logo[1].padEnd(logoWidth), palette, phase + 3) + gap + rightRow1];\n'
    '}'
)
NEW4 = (
    'function renderDanceWelcomeHeader(logo, textWidth, rightRow1, rightRow1Text) {\n'
    '\tconst phase = currentDanceView?.phase ?? 0;\n'
    '\tconst palette = getDanceRainbowPalette();\n'
    '\tconst logoWidth = Math.max(...logo.map((row) => visibleWidth(row)));\n'
    '\tconst gap = "  ";\n'
    '\tconst rowWidth = logoWidth + 2 + textWidth;\n'
    '\tconst rightRow0 = truncateToWidth(rainbowText("Welcome to Kimi Code!", palette, phase, true, logoWidth + 2, rowWidth), textWidth, "…");\n'
    '\tconst rightRow1Shimmer = rightRow1Text === void 0 ? rightRow1 : truncateToWidth(rainbowText(rightRow1Text, palette, phase + 1, false, logoWidth + 2, rowWidth), textWidth, "…");\n'
    '\treturn [rainbowText(logo[0].padEnd(logoWidth), SHIMMER_LOGO_PALETTE, phase, false, 0, rowWidth) + gap + rightRow0, rainbowText(logo[1].padEnd(logoWidth), SHIMMER_LOGO_PALETTE, phase + 1, false, 0, rowWidth) + gap + rightRow1Shimmer];\n'
    '}'
)

# ---------- E5：帧表 110ms → 33ms（≈30 FPS） ----------
OLD5 = (
    '\t\t\tthis.frameTimer = setInterval(() => {\n'
    '\t\t\t\tthis.currentPhase += 1;\n'
    '\t\t\t\tthis.requestRender();\n'
    '\t\t\t}, 110);'
)
NEW5 = (
    '\t\t\tthis.frameTimer = setInterval(() => {\n'
    '\t\t\t\tthis.currentPhase += 1;\n'
    '\t\t\t\tthis.requestRender();\n'
    '\t\t\t}, 33);'
)

# ---------- E6：welcome.ts 抽出 rightRow1Text 原文 ----------
OLD6 = (
    '\t\t\tconst rightRow1 = truncateToWidth(dim(isLoggedOut ? "Run /login or /provider to get started." : "Send /help for help information."), textWidth, "…");'
)
NEW6 = (
    '\t\t\tconst rightRow1Text = isLoggedOut ? "Run /login or /provider to get started." : "Send /help for help information.";\n'
    '\t\t\tconst rightRow1 = truncateToWidth(dim(rightRow1Text), textWidth, "…");'
)

# ---------- E7：welcome.ts 调用点传 rightRow1Text ----------
OLD7 = (
    '\t\t\tif (isRainbowDancing()) renderedHeaderLines = renderDanceWelcomeHeader(logo, textWidth, rightRow1);'
)
NEW7 = (
    '\t\t\tif (isRainbowDancing()) renderedHeaderLines = renderDanceWelcomeHeader(logo, textWidth, rightRow1, rightRow1Text);'
)

# ---------- E8：welcome.ts 信息行整板流光 ----------
OLD8 = (
    '\t\t\tif (this.state.mcpServersSummary) infoLines.push(labelStyle("MCP:       ") + this.state.mcpServersSummary);\n'
    '\t\t\tconst contentLines = [\n'
    '\t\t\t\t...renderedHeaderLines,\n'
    '\t\t\t\t"",\n'
    '\t\t\t\t...infoLines\n'
    '\t\t\t];'
)
NEW8 = (
    '\t\t\tif (this.state.mcpServersSummary) infoLines.push(labelStyle("MCP:       ") + this.state.mcpServersSummary);\n'
    '\t\t\tconst infoRaw = [\n'
    '\t\t\t\t"Directory: " + this.state.workDir,\n'
    '\t\t\t\t"Session:   " + this.state.sessionId,\n'
    '\t\t\t\t"Model:     " + (effectiveActiveModel?.displayName ?? effectiveActiveModel?.model ?? this.state.model ?? "not set, run /login or /provider"),\n'
    '\t\t\t\t"Version:   " + this.state.version\n'
    '\t\t\t];\n'
    '\t\t\tif (this.state.mcpServersSummary) infoRaw.push("MCP:       " + this.state.mcpServersSummary);\n'
    '\t\t\tconst contentLines = [\n'
    '\t\t\t\t...renderedHeaderLines,\n'
    '\t\t\t\t"",\n'
    '\t\t\t\t...(isRainbowDancing() ? infoRaw.map((line, i) => shimmerBannerLine(line, 3 + i, false, innerWidth)) : infoLines)\n'
    '\t\t\t];'
)

# ---------- E9：banner.ts tips 横幅流光 ----------
OLD9 = (
    '\t\tfor (let i = 0; i < mainSegments.length; i++) {\n'
    '\t\t\tconst wrapped = wrapTextWithAnsi(mainSegments[i], bodyContentWidth);\n'
    '\t\t\tfor (let j = 0; j < wrapped.length; j++) {\n'
    '\t\t\t\tconst boldLine = main(wrapped[j]);\n'
    '\t\t\t\tif (i === 0 && j === 0 && showTag) result.push(tagDisplay + boldLine);\n'
    '\t\t\t\telse result.push(bodyIndent + boldLine);\n'
    '\t\t\t}\n'
    '\t\t}\n'
    '\t\tfor (const sub of subSegments) {\n'
    '\t\t\tconst wrapped = wrapTextWithAnsi(sub, descContentWidth <= 0 ? bodyContentWidth : descContentWidth);\n'
    '\t\t\tfor (const line of wrapped) result.push(descIndent + dim(line));\n'
    '\t\t}'
)
NEW9 = (
    '\t\tfor (let i = 0; i < mainSegments.length; i++) {\n'
    '\t\t\tconst wrapped = wrapTextWithAnsi(mainSegments[i], bodyContentWidth);\n'
    '\t\t\tfor (let j = 0; j < wrapped.length; j++) {\n'
    '\t\t\t\tconst boldLine = isRainbowDancing() ? shimmerBannerLine(wrapped[j], result.length, true, width) : main(wrapped[j]);\n'
    '\t\t\t\tif (i === 0 && j === 0 && showTag) result.push(tagDisplay + boldLine);\n'
    '\t\t\t\telse result.push(bodyIndent + boldLine);\n'
    '\t\t\t}\n'
    '\t\t}\n'
    '\t\tfor (const sub of subSegments) {\n'
    '\t\t\tconst wrapped = wrapTextWithAnsi(sub, descContentWidth <= 0 ? bodyContentWidth : descContentWidth);\n'
    '\t\t\tfor (const line of wrapped) result.push(descIndent + (isRainbowDancing() ? shimmerBannerLine(line, result.length, false, width) : dim(line)));\n'
    '\t\t}'
)

EDITS = [
    ('E1 rainbowText → shimmer 核心 v2', OLD1, NEW1),
    ('E2 settle(hold) 永续流动', OLD2, NEW2),
    ('E3 installRainbowDance 常驻自启', OLD3, NEW3),
    ('E4 renderDanceWelcomeHeader 同步+连续x', OLD4, NEW4),
    ('E5 帧表 110→33 (30FPS)', OLD5, NEW5),
    ('E6 welcome 抽出 rightRow1Text', OLD6, NEW6),
    ('E7 welcome 传 rightRow1Text', OLD7, NEW7),
    ('E8 welcome 信息行整板流光', OLD8, NEW8),
    ('E9 tips 横幅流光', OLD9, NEW9),
]
MARK = 'SHIMMER_CORE_RGB'

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SRC
    dst = sys.argv[2] if len(sys.argv) > 2 else DST
    text = open(src, 'rb').read().decode('utf-8')

    if MARK in text:
        print('already patched: 已含 SHIMMER 标记，原样写出')
        out = text
    else:
        for name in ('shimmerParseHex', 'shimmerToHex', 'shimmerMix', 'shimmerCharWidth', 'shimmerSample', 'shimmerBannerLine'):
            if name in text:
                print(f'FATAL: 标识符 {name} 已存在于 bundle，拒绝补丁（防命名冲突）')
                sys.exit(1)
        out = text
        for label, old, new in EDITS:
            hits = out.count(old)
            print(f'anchor [{label}]: {hits} hit(s)')
            if hits != 1:
                print(f'FATAL: 锚定命中数={hits}（期望 1），拒绝补丁')
                sys.exit(1)
            out = out.replace(old, new)
        print(f'{len(EDITS)}/{len(EDITS)} edits applied')

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(out.encode('utf-8'))
    open(SNIPPET, 'wb').write(NEW1.encode('utf-8'))
    delta = len(out.encode('utf-8')) - len(text.encode('utf-8'))
    print(f'-> {dst} ({len(out.encode("utf-8")):,} bytes, delta={delta:+d})')
    print(f'-> {SNIPPET} (单测取样)')

if __name__ == '__main__':
    main()
