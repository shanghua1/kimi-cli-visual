# -*- coding: utf-8 -*-
"""任务A 零风险首补丁：DARK_RAINBOW 8 色 → 紫金波浪色板（等长替换，不改任何长度）。

用法: python patch_palette.py [in.cjs] [out.cjs]
默认: work/main.orig.cjs -> build/main.palette.cjs
锚定: init_dance 内 `DARK_RAINBOW = [ ... ];` 整块，必须全文件唯一。
幂等: 已是新色板则报告 already patched 并原样写出。"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'work', 'main.orig.cjs')
DST = os.path.join(HERE, 'build', 'main.palette.cjs')

OLD = [
    '#4FA8FF', '#5BC0BE', '#4EC87E', '#E8A838',
    '#FFCB6B', '#C678B8', '#A274D9', '#7C8DFF',
]
# 紫金玫波浪：紫→堇→玫瑰粉→主紫→金（峰）→主紫→玫瑰粉→堇
# （第 3/7 位 #FF8799 玫瑰粉对称拱卫金峰，仅两席为粉，紫为体、金为峰、粉为缀）
NEW = [
    '#8A6FC0', '#9D8BD4', '#FF8799', '#CD96CD',
    '#EAC364', '#CD96CD', '#FF8799', '#9D8BD4',
]
assert all(len(c) == 7 for c in OLD + NEW), '色板必须等长 (#RRGGBB)'

def block(colors):
    return 'DARK_RAINBOW = [\n' + ''.join(f'\t\t"{c}",\n' for c in colors)[:-2] + '\n\t];'

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SRC
    dst = sys.argv[2] if len(sys.argv) > 2 else DST
    text = open(src, 'rb').read().decode('utf-8')

    old_block, new_block = block(OLD), block(NEW)
    n_old, n_new = text.count(old_block), text.count(new_block)
    print(f'anchor hits: old={n_old} new={n_new}')
    if n_new == 1 and n_old == 0:
        print('already patched: 色板已是紫金，原样写出')
        out = text
    elif n_old == 1 and n_new == 0:
        out = text.replace(old_block, new_block)
        for o, n in zip(OLD, NEW):
            if o != n:
                print(f'  {o} -> {n}')
        print('palette patched (equal-length, 8/8)')
    else:
        print('FATAL: 锚定不唯一或新旧混杂，拒绝补丁')
        sys.exit(1)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(out.encode('utf-8'))
    delta = len(out.encode('utf-8')) - len(text.encode('utf-8'))
    print(f'-> {dst} ({len(out.encode("utf-8")):,} bytes, delta={delta:+d})')

if __name__ == '__main__':
    main()
