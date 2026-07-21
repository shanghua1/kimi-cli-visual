'use strict';
// 流光注入代码单测：eval dance-snippet.js（chalk 用记录型桩替代），验证：
// 1) 可见字符守恒（剥掉标记后等于原文）  2) 相位推进 → 光带移动  3) 扫过全程出现近银白核心与加粗
// 4) 空白严格遮罩（空格不被上色）  5) 同相位确定性  6) CJK 宽字符不破坏文本
const fs = require('fs');
const path = require('path');

const chalk = {
  hex(h) {
    const f = (c) => `«${h}»${c}«/»`;
    f.bold = (c) => `«${h}:b»${c}«/»`;
    return f;
  },
};
const snippet = fs.readFileSync(path.join(__dirname, 'build', 'dance-snippet.js'), 'utf8');
eval(snippet + '\nmodule.exports = { rainbowText, shimmerSample, SHIMMER_FRAME_MS, SHIMMER_LOGO_PALETTE };');
const { rainbowText, shimmerSample, SHIMMER_FRAME_MS, SHIMMER_LOGO_PALETTE } = module.exports;

const PALETTE = ['#8A6FC0', '#9D8BD4', '#FF8799', '#CD96CD', '#EAC364', '#CD96CD', '#FF8799', '#9D8BD4'];
const TEXT = 'Welcome to Kimi Code!';
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

// 3) 核心增亮：逐字符追踪全程相位，最高亮度须显著超过其基色（amount 上限 0.62 是原作的克制设计）
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
  // 去掉所有 «…»X«/» 包裹后，剩余字符应只剩未上色的；直接查 " » " 型裸空格不行，改查标记内无空格
  for (const m of out.matchAll(/«#[0-9a-f]{6}(?::b)?»(.*?)«\/»/g)) if (m[1] === ' ') spaceClean = false;
}
check('空白严格遮罩', spaceClean);

// 5) 同相位确定性
check('同相位确定性', rainbowText(TEXT, PALETTE, 7, false) === rainbowText(TEXT, PALETTE, 7, false));

// 6) CJK 宽字符
check('CJK 字符守恒', strip(rainbowText('流光测试ab', PALETTE, 9, false)) === '流光测试ab');

// 7) 采样函数与原作一致的关键数值（核心/肩光/拖尾/前导/远端）
const at = (proj) => shimmerSample(proj, 0.24 / (1.2 * 0.34)).intensity; // head=0 时 distance=projection
const approx = (a, b, eps = 1e-9) => Math.abs(a - b) < eps;
check('核心强度=1', approx(at(0), 1));
check('肩光下沿≈0.26', approx(at(0.105), 0.26));
check('拖尾末端→0', at(0.34) < 1e-6);
check('远端无强度', approx(at(0.9), 0));
check('前导微光有界', at(-0.15) > 0 && at(-0.15) <= 0.14 + 1e-9);

// 8) v2 同步保证：同一视觉行上，x 相同则颜色相同（跨段连续坐标系）
const MONO = ['#CD96CD'];
const row = rainbowText('▐█▛█▛█▌  Welcome', MONO, 7, false, 0, 40);
const segLogo = colors(rainbowText('▐█▛█▛█▌', MONO, 7, false, 0, 40));
const segText = colors(rainbowText('Welcome', MONO, 7, false, 8, 40));
const rowColors = colors(row);
const joined = [...segLogo, ...segText];
check('同行跨段颜色逐位一致', rowColors.length === joined.length && rowColors.every((c, i) => c.hex === joined[i].hex && c.bold === joined[i].bold));

// 9) v2 帧率：33ms（≈30 FPS）
check('SHIMMER_FRAME_MS=33', SHIMMER_FRAME_MS === 33);

// 10) v2.3 全局金高光 + logo 七阶自然渐变
check('logo 色板无玫粉(#FF8799)', !SHIMMER_LOGO_PALETTE.includes('#FF8799'));
check('logo 色板为紫金七阶', SHIMMER_LOGO_PALETTE.join(',') === '#473C8B,#6A58A6,#9D8BD4,#CD96CD,#EAC364,#B7A6E8,#8A6FC0');
const logoLums = SHIMMER_LOGO_PALETTE.map(lum);
check('logo 渐变自然(亮度递升至金峰后回落)', logoLums.slice(0, 5).every((v, i) => i === 0 || v > logoLums[i - 1]) && logoLums[5] < logoLums[4] && logoLums[6] < logoLums[5]);
// 金高光：核心经过处 R>B（紫基 B>R 被香槟金压过），logo 与文字同享
const logoCoreCell = colors(rainbowText('█', ['#473C8B'], 17.82, false, 0, 1))[0];
const logoCoreNum = parseInt(logoCoreCell.hex.slice(1), 16);
check('logo 核心泛金(R>B)', (logoCoreNum >> 16 & 255) > (logoCoreNum & 255));
const textCoreCell = colors(rainbowText('W', ['#473C8B'], 17.82, false, 0, 1))[0];
const textCoreNum = parseInt(textCoreCell.hex.slice(1), 16);
check('文字核心亦泛金(R>B)', (textCoreNum >> 16 & 255) > (textCoreNum & 255));

console.log(failures === 0 ? '\nALL TESTS PASSED' : `\n${failures} FAILURE(S)`);
process.exit(failures === 0 ? 0 : 1);
