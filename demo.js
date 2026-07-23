/**
 * Golden Night 字符流光 · 终端演示。
 * 用法: node demo.js           30 FPS 动画（Ctrl+C 退出）
 *       node demo.js --frames 90   跑 90 帧后自动退出
 * 需要支持 24-bit 真彩的终端（Windows Terminal / WezTerm / iTerm2 等）。
 */
'use strict';
const {
	rainbowText,
	SHIMMER_FRAME_MS,
	SHIMMER_LOGO_PALETTE,
	SHIMMER_EDITOR_HIGHLIGHT,
	SHIMMER_EDITOR_FRAME_PALETTE,
} = require('./shimmer-core.js');

const FLOW_PALETTE = ['#8A6FC0', '#9D8BD4', '#FF8799', '#CD96CD', '#EAC364', '#CD96CD', '#FF8799', '#9D8BD4'];

const LOGO = ['▐█▛█▛█▌', '▝▜▙▜▙▘ '];
const TITLE = 'Golden Night  字符流光';
const INFO = [
	'Palette:  紫为体 · 金为饰 · 玫粉为缀',
	'Sweep:    core / shoulder / trail / lead',
	'Row lag:  +1 相位/行 → 对角推进',
	'CJK:      宽字符按 2 格计入光带投影',
];
const BORDER_W = 46;

function frameLines(phase) {
	const logoW = 7;
	const rowWidth = logoW + 2 + [...TITLE].reduce((n, c) => n + (c.codePointAt(0) > 0x2E7F ? 2 : 1), 0);
	const lines = [];
	// logo 七阶自渐变 + 标题共享同一坐标系（光带跨段连续）
	lines.push('  ' + rainbowText(LOGO[0], SHIMMER_LOGO_PALETTE, phase, false, 0, rowWidth)
		+ '  ' + rainbowText(TITLE, FLOW_PALETTE, phase, true, logoW + 2, rowWidth));
	lines.push('  ' + rainbowText(LOGO[1], SHIMMER_LOGO_PALETTE, phase + 1, false, 0, rowWidth));
	lines.push('');
	// 信息行：行间 +1 相位，斜向扫光
	INFO.forEach((line, i) => lines.push('  ' + rainbowText(line, FLOW_PALETTE, phase + 3 + i, false, 60)));
	lines.push('');
	// 输入框边框：玫金循环基色 + 隐没暗带（顶/侧/底错相位，光带绕框而行）
	const top = '╭' + '─'.repeat(BORDER_W) + '╮';
	const bottom = '╰' + '─'.repeat(BORDER_W) + '╯';
	const paintEdge = (s, frameRow) =>
		rainbowText(s, SHIMMER_EDITOR_FRAME_PALETTE, phase + frameRow * 9, false, 0, 0, SHIMMER_EDITOR_HIGHLIGHT);
	lines.push('  ' + paintEdge(top, 0));
	lines.push('  ' + paintEdge('│', 1) + ' > 一道影梭沿边框缓行…'.padEnd(BORDER_W - 10) + paintEdge('│', 1));
	lines.push('  ' + paintEdge(bottom, 2));
	return lines;
}

function main() {
	process.stdout.on('error', (e) => { if (e.code === 'EPIPE') process.exit(0); throw e; });
	const argIdx = process.argv.indexOf('--frames');
	const maxFrames = argIdx > -1 ? Math.max(1, Number(process.argv[argIdx + 1]) || 90) : Infinity;
	const animated = process.stdout.isTTY && maxFrames === Infinity;
	let phase = 0;
	const height = frameLines(0).length;

	const draw = () => {
		const out = frameLines(phase).join('\n');
		if (phase > 0 && animated) process.stdout.write(`\x1b[${height}A`);
		process.stdout.write(out + '\n');
		phase++;
	};

	if (!animated) {
		// 非 TTY 或指定帧数：逐帧打印（可用于冒烟测试）
		for (let i = 0; i < Math.min(maxFrames, 3); i++) draw();
		return;
	}
	process.stdout.write('\x1b[?25l'); // 隐藏光标
	const timer = setInterval(draw, SHIMMER_FRAME_MS);
	const restore = () => {
		clearInterval(timer);
		process.stdout.write('\x1b[?25h\n');
		process.exit(0);
	};
	process.on('SIGINT', restore);
	process.on('SIGTERM', restore);
	draw();
}

main();
