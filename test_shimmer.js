'use strict';
// 流光核心单测（node test_shimmer.js）：注入记录型样式桩，验证：
// 1) 可见字符守恒  2) 相位推进 → 光带移动  3) 核心增亮与加粗  4) 空白严格遮罩
// 5) 同相位确定性  6) CJK 宽字符  7) 采样数值  8) 同行跨段坐标一致
// 9) 高光覆盖（隐没暗带 / 对称光带 / 窄带 widths / boldFloor）
const core = require('./shimmer-core.js');
core.setShimmerStyler((h) => {
  const f = (c) => `«${h}»${c}«/»`;
  f.bold = (c) => `«${h}:b»${c}«/»`;
  return f;
});
const { rainbowText, shimmerSample, SHIMMER_FRAME_MS, SHIMMER_LOGO_PALETTE, SHIMMER_EDITOR_HIGHLIGHT, SHIMMER_EDITOR_FRAME_PALETTE } = core;

const PALETTE = ['#8A6FC0', '#9D8BD4', '#FF8799', '#CD96CD', '#EAC364', '#CD96CD', '#FF8799', '#9D8BD4'];
const TEXT = 'Golden Night shimmer!';
const strip = (s) => s.replace(/«#[0-9a-f]{6}(?::b)?»|«\/»/g, '');
const colors = (s) => [...s.matchAll(/«(#[0-9a-f]{6})(:b)?»/g)].map((m) => ({ hex: m[1], bold: !!m[2] }));

let failures = 0;
const check = (name, ok, detail = '') => {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + detail : ''}`);
  if (!ok) failures++;
};

// 1) 字符守恒（多相位）
let conserve = true;
for (let p = 0; p < 50; p++) if (strip(rainbowText(TEXT, PALETTE, p, false)) !== TEXT) conserve = false;
check('可见字符守恒(0..49 相位)', conserve);

// 2) 光带移动：不同相位颜色分布不同
const seq = [0, 8, 16, 24].map((p) => colors(rainbowText(TEXT, PALETTE, p, false)).map((c) => c.hex).join(','));
check('相位推进光带移动', new Set(seq).size === seq.length);

// 3) 核心增亮：逐字符追踪全程相位，最高亮度须显著超过其基色
const lum = (hex) => {
  const n = parseInt(hex.slice(1), 16);
  return 0.2126 * (n >> 16 & 255) + 0.7152 * (n >> 8 & 255) + 0.0722 * (n & 255);
};
let sawBrighten = false, sawBold = false;
const baseLums = colors(rainbowText(TEXT, PALETTE, 10_000, false)).map((c) => lum(c.hex)); // 相位够大时 head 已出界，全为基色
for (let p = 0; p < 60; p++) {
  colors(rainbowText(TEXT, PALETTE, p, false)).forEach((c, i) => {
    if (baseLums[i] !== void 0 && lum(c.hex) > baseLums[i] + 25) sawBrighten = true;
    if (c.bold) sawBold = true;
  });
}
check('核心经过显著增亮(>25)', sawBrighten);
check('核心邻域出现加粗', sawBold);

// 4) 空白遮罩：空格永不带颜色标记
let spaceClean = true;
for (let p = 0; p < 50; p++) {
  const out = rainbowText(TEXT, PALETTE, p, false);
  for (const m of out.matchAll(/«#[0-9a-f]{6}(?::b)?»(.*?)«\/»/g)) if (m[1] === ' ') spaceClean = false;
}
check('空白严格遮罩', spaceClean);

// 5) 同相位确定性
check('同相位确定性', rainbowText(TEXT, PALETTE, 7, false) === rainbowText(TEXT, PALETTE, 7, false));

// 6) CJK 宽字符
check('CJK 字符守恒', strip(rainbowText('流光测试ab', PALETTE, 9, false)) === '流光测试ab');

// 7) 采样函数关键数值（核心/肩光/拖尾/前导/远端）
const at = (proj) => shimmerSample(proj, 0.24 / (1.2 * 0.34)).intensity; // head=0 时 distance=projection
const approx = (a, b, eps = 1e-9) => Math.abs(a - b) < eps;
check('核心强度=1', approx(at(0), 1));
check('肩光下沿≈0.26', approx(at(0.105), 0.26));
check('拖尾末端→0', at(0.34) < 1e-6);
check('远端无强度', approx(at(0.9), 0));
check('前导微光有界', at(-0.15) > 0 && at(-0.15) <= 0.14 + 1e-9);

// 8) 同一视觉行上，x 相同则颜色相同（跨段连续坐标系）
const MONO = ['#CD96CD'];
const row = rainbowText('▐█▛█▛█▌  Shimmer', MONO, 7, false, 0, 40);
const segLogo = colors(rainbowText('▐█▛█▛█▌', MONO, 7, false, 0, 40));
const segText = colors(rainbowText('Shimmer', MONO, 7, false, 8, 40));
const rowColors = colors(row);
const joined = [...segLogo, ...segText];
check('同行跨段颜色逐位一致', rowColors.length === joined.length && rowColors.every((c, i) => c.hex === joined[i].hex && c.bold === joined[i].bold));

// 9) 帧率常量：33ms（≈30 FPS）
check('SHIMMER_FRAME_MS=33', SHIMMER_FRAME_MS === 33);

// 10) 全局金高光 + logo 七阶自然渐变
check('logo 色板无玫粉(#FF8799)', !SHIMMER_LOGO_PALETTE.includes('#FF8799'));
check('logo 色板为紫金七阶', SHIMMER_LOGO_PALETTE.join(',') === '#473C8B,#6A58A6,#9D8BD4,#CD96CD,#EAC364,#B7A6E8,#8A6FC0');
const logoLums = SHIMMER_LOGO_PALETTE.map(lum);
check('logo 渐变自然(亮度递升至金峰后回落)', logoLums.slice(0, 5).every((v, i) => i === 0 || v > logoLums[i - 1]) && logoLums[5] < logoLums[4] && logoLums[6] < logoLums[5]);
// 金高光：核心经过处 R>B（紫基 B>R 被香槟金压过）
const logoCoreCell = colors(rainbowText('█', ['#473C8B'], 17.82, false, 0, 1))[0];
const logoCoreNum = parseInt(logoCoreCell.hex.slice(1), 16);
check('logo 核心泛金(R>B)', (logoCoreNum >> 16 & 255) > (logoCoreNum & 255));
const textCoreCell = colors(rainbowText('W', ['#473C8B'], 17.82, false, 0, 1))[0];
const textCoreNum = parseInt(textCoreCell.hex.slice(1), 16);
check('文字核心亦泛金(R>B)', (textCoreNum >> 16 & 255) > (textCoreNum & 255));

// 11) 高光覆盖三区：隐没暗带核心柔沉、拖尾染玫、boldFloor 放宽加粗、分段基色板
const chan = (hex, i) => parseInt(hex.slice(1), 16) >> (16 - i * 8) & 255;
{
  const editorCore = colors(rainbowText('─', ['#6A58A6'], 17.82, false, 0, 1, SHIMMER_EDITOR_HIGHLIGHT))[0];
  check('暗带核心半沉柔暗(亮度比0.4~0.7)', (() => { const r = lum(editorCore.hex) / lum('#6A58A6'); return r > 0.4 && r < 0.7; })());
  const goldCore = colors(rainbowText('─', ['#6A58A6'], 17.82, false, 0, 1))[0];
  check('默认核心仍金(R>B)', chan(goldCore.hex, 0) > chan(goldCore.hex, 2));
  // 相位 7.43 ≈ 加粗权重 0.21 处：editor boldFloor 0.1 → 加粗；默认 0.24 → 不加粗
  const editorBold = colors(rainbowText('─', ['#6A58A6'], 7.43, false, 0, 1, SHIMMER_EDITOR_HIGHLIGHT))[0];
  const plainBold = colors(rainbowText('─', ['#6A58A6'], 7.43, false, 0, 1))[0];
  check('boldFloor 放宽加粗(0.21∈(0.1,0.24))', editorBold.bold === true && plainBold.bold === false);
  // 相位 3 ≈ 拖尾区（distance∈(0.105,0.34]）；对照组=同肩光但无 trail 色
  const roseTrail = colors(rainbowText('─', ['#6A58A6'], 3, false, 0, 1, SHIMMER_EDITOR_HIGHLIGHT))[0];
  const goldTrail = colors(rainbowText('─', ['#6A58A6'], 3, false, 0, 1, { core: [252, 253, 250], shoulder: [255, 233, 179] }))[0];
  check('暗带拖尾玫于金尾(B更低)', chan(roseTrail.hex, 2) < chan(goldTrail.hex, 2));
  check('玫金紫循环基色板', SHIMMER_EDITOR_FRAME_PALETTE.join(',') === '#FF8799,#CE89B7,#9D8BD4,#C4A79C,#EAC364,#D1B5A6,#B7A6E8,#DB97C1');
}

// 12) 对称光带：symmetric 前缘镜像后缘（同宽同强）、前缘染玫；widths 窄带
{
  const t0 = 0.24 / (1.2 * 0.34); // head=0 的时刻，distance 即 projection
  const symLead = shimmerSample(-0.15, t0, true).intensity;   // distance=-0.15 前缘
  const rawLead = shimmerSample(-0.15, t0, false).intensity;
  check('symmetric 前缘增强(>原前缘)', symLead > rawLead);
  check('symmetric 前缘≈后缘镜像(0.17)', Math.abs(symLead - 0.26 * Math.pow(1 - (0.15 - 0.105) / 0.235, 2)) < 1e-9);
  check('symmetric 前缘拓宽至 0.34', shimmerSample(-0.3, t0, true).intensity > 0 && approx(shimmerSample(-0.3, t0, false).intensity, 0));
  // widths 参：窄带 0.17，distance=0.2 出界；默认 0.34 仍在带内
  check('widths 收窄光带(0.2 出界)', approx(shimmerSample(0.2, t0, true, SHIMMER_EDITOR_HIGHLIGHT.widths).intensity, 0) && shimmerSample(0.2, t0, true).intensity > 0);
  // 相位 11.14 ≈ 前缘区（暗带窄带内强信号）；对照组此处为肩光区（亮）
  const roseLead = colors(rainbowText('─', ['#6A58A6'], 11.14, false, 0, 1, SHIMMER_EDITOR_HIGHLIGHT))[0];
  const goldLead = colors(rainbowText('─', ['#6A58A6'], 11.14, false, 0, 1, { core: [252, 253, 250], shoulder: [255, 233, 179] }))[0];
  check('暗带前缘隐没变暗(亮度低3+)', lum(goldLead.hex) - lum(roseLead.hex) > 3);
}

console.log(failures === 0 ? '\nALL TESTS PASSED' : `\n${failures} FAILURE(S)`);
process.exit(failures === 0 ? 0 : 1);
