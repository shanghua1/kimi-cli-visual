/**
 * Golden Night shimmer core — 紫金玫字符流光算法（终端 ANSI 真彩）。
 *
 * 零依赖独立模块：静态色板为底，一道光带沿行方向扫过，
 * 核心增亮、肩光过渡、拖尾/前导衰减，可对称、可窄带、可反转为暗带。
 * 移植自作者的 text-shimmer.js（ncm-visual-lab）。MIT License。
 */
'use strict';

const SHIMMER_CORE_RGB = [255, 233, 179];
const SHIMMER_SHOULDER_RGB = [234, 195, 100];
const SHIMMER_CYCLE_SPAN = 1.72;
const SHIMMER_RATE = 0.34;
const SHIMMER_SPEED = 1.2;
const SHIMMER_STRENGTH = 1;
const SHIMMER_FRAME_MS = 33;
const SHIMMER_LOGO_PALETTE = ["#473C8B", "#6A58A6", "#9D8BD4", "#CD96CD", "#EAC364", "#B7A6E8", "#8A6FC0"];
const SHIMMER_EDITOR_HIGHLIGHT = { core: [18, 14, 26], shoulder: [42, 30, 58], trail: [58, 38, 72], strength: 1, cap: 0.55, boldFloor: 0.1, widths: { core: 0.022, shoulder: 0.07, edge: 0.17 } };
const SHIMMER_EDITOR_FRAME_PALETTE = ["#FF8799", "#CE89B7", "#9D8BD4", "#C4A79C", "#EAC364", "#D1B5A6", "#B7A6E8", "#DB97C1"];

function shimmerParseHex(hex) {
	const n = Number.parseInt(String(hex).replace("#", ""), 16);
	return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function shimmerToHex(rgb) {
	return "#" + rgb.map((c) => Math.max(0, Math.min(255, Math.round(c))).toString(16).padStart(2, "0")).join("");
}
function shimmerMix(from, to, amount) {
	const r = Math.max(0, Math.min(1, amount));
	return from.map((c, i) => c + (to[i] - c) * r);
}
function shimmerCharWidth(char) {
	const code = char.codePointAt(0);
	if (code <= 31 || (code >= 127 && code <= 159)) return 0;
	if (code >= 4352 && (code <= 4447 || code === 9001 || code === 9002 || (code >= 11904 && code <= 42191 && code !== 12351) || (code >= 44032 && code <= 55203) || (code >= 63744 && code <= 64255) || (code >= 65040 && code <= 65049) || (code >= 65072 && code <= 65135) || (code >= 65280 && code <= 65376) || (code >= 65504 && code <= 65510) || (code >= 127744 && code <= 129535))) return 2;
	return 1;
}

/** 内置 ANSI 真彩样式器；可注入替换（单测用记录桩）。 */
function defaultStyler(hex) {
	const [r, g, b] = shimmerParseHex(hex);
	const paint = (s) => `\x1b[38;2;${r};${g};${b}m${s}\x1b[39m`;
	paint.bold = (s) => `\x1b[1;38;2;${r};${g};${b}m${s}\x1b[22;39m`;
	return paint;
}
let styler = defaultStyler;
function setShimmerStyler(fn) { styler = fn ?? defaultStyler; }

/** Diagonal sweep intensity at a normalized position.
 * symmetric=true mirrors the trail onto the lead side; widths overrides band widths. */
function shimmerSample(projection, time, symmetric = false, widths) {
	const coreW = widths?.core ?? 0.035;
	const shoulderW = widths?.shoulder ?? 0.105;
	const edgeW = widths?.edge ?? 0.34;
	const head = ((time * SHIMMER_SPEED * SHIMMER_RATE) % SHIMMER_CYCLE_SPAN + SHIMMER_CYCLE_SPAN) % SHIMMER_CYCLE_SPAN - 0.24;
	const distance = projection - head;
	const ad = Math.abs(distance);
	if (ad <= coreW) return { intensity: 1, core: true, distance };
	if (ad <= shoulderW) {
		const shoulder = 1 - (ad - coreW) / (shoulderW - coreW);
		return { intensity: 0.26 + shoulder * 0.48, core: false, distance };
	}
	if (distance > shoulderW && distance <= edgeW) {
		const trail = 1 - (distance - shoulderW) / (edgeW - shoulderW);
		return { intensity: 0.26 * trail * trail, core: false, distance };
	}
	if (distance < -shoulderW && ad <= (symmetric ? edgeW : 0.19)) {
		const edge = symmetric ? edgeW : 0.19;
		const peak = symmetric ? 0.26 : 0.14;
		const lead = 1 - (ad - shoulderW) / (edge - shoulderW);
		return { intensity: peak * lead * lead, core: false, distance };
	}
	return { intensity: 0, core: false, distance };
}

/** Paint a string with the Golden Night sweep: static palette base, light band gliding over it.
 * xOffset/totalWidth let multiple segments of one visual row share a single coordinate system.
 * highlight 可覆盖高光三色（core/shoulder/trail）与 strength/cap/boldFloor/widths。 */
function rainbowText(text, colors, offset = 0, bold = false, xOffset = 0, totalWidth = 0, highlight) {
	const highlightCore = highlight?.core ?? SHIMMER_CORE_RGB;
	const highlightShoulder = highlight?.shoulder ?? SHIMMER_SHOULDER_RGB;
	const highlightTrail = highlight?.trail;
	const chars = Array.from(text);
	const columns = [];
	let totalCells = 0;
	for (const char of chars) {
		columns.push(totalCells);
		totalCells += Math.max(1, shimmerCharWidth(char));
	}
	const span = Math.max(totalWidth, xOffset + totalCells);
	const time = offset * SHIMMER_FRAME_MS / 1000;
	let colorIndex = 0;
	return chars.map((char, index) => {
		if (char === " ") return char;
		const base = shimmerParseHex(colors[colorIndex % colors.length] ?? colors[0]);
		colorIndex++;
		const projection = span <= 1 ? 0 : (xOffset + columns[index]) / (span - 1) * 0.72;
		const sample = shimmerSample(projection, time, highlightTrail !== void 0, highlight?.widths);
		if (sample.intensity <= 0.006) {
			const style = styler(shimmerToHex(base));
			return bold ? style.bold(char) : style(char);
		}
		const bandColor = sample.core
			? shimmerMix(highlightShoulder, highlightCore, 0.86)
			: Math.abs(sample.distance) > (highlight?.widths?.shoulder ?? 0.105) && highlightTrail !== void 0
				? shimmerMix(highlightShoulder, highlightTrail, 0.45)
				: shimmerMix(highlightShoulder, highlightCore, 0.28);
		const amount = Math.min(highlight?.cap ?? 0.72, sample.intensity * (sample.core ? 0.62 : 0.3) * SHIMMER_STRENGTH * (highlight?.strength ?? 1));
		const weight = Math.exp(-Math.pow(sample.distance / 0.112, 2));
		const style = styler(shimmerToHex(shimmerMix(base, bandColor, amount)));
		return bold || sample.core || weight > (highlight?.boldFloor ?? 0.24) ? style.bold(char) : style(char);
	}).join("");
}

module.exports = {
	SHIMMER_CORE_RGB,
	SHIMMER_SHOULDER_RGB,
	SHIMMER_CYCLE_SPAN,
	SHIMMER_RATE,
	SHIMMER_SPEED,
	SHIMMER_STRENGTH,
	SHIMMER_FRAME_MS,
	SHIMMER_LOGO_PALETTE,
	SHIMMER_EDITOR_HIGHLIGHT,
	SHIMMER_EDITOR_FRAME_PALETTE,
	shimmerParseHex,
	shimmerToHex,
	shimmerMix,
	shimmerCharWidth,
	shimmerSample,
	rainbowText,
	setShimmerStyler,
};
