# -*- coding: utf-8 -*-
"""重建 SEA blob：header(改 main_len) + 新 code + tail，产出 .bin 供注入。
用法: python rebuild_blob.py <new_main.cjs> <out_blob.bin>
幂等: 纯函数式拼装，重跑同输入同输出。"""
import json, os, sys
from sea_pe import parse_blob_header, build_blob_header

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'work')

def main():
    new_main, out_bin = sys.argv[1], sys.argv[2]
    layout = json.load(open(os.path.join(WORK, 'layout.json')))
    h = layout['header']
    old_len = h['main_len']

    code = open(new_main, 'rb').read()
    tail = open(os.path.join(WORK, 'tail.bin'), 'rb').read()
    assert len(tail) == layout['tail_len'], 'tail 长度与提取时不符'

    header = build_blob_header(h, len(code))
    blob = header + code + tail
    os.makedirs(os.path.dirname(out_bin), exist_ok=True)
    open(out_bin, 'wb').write(blob)

    delta = len(code) - old_len
    print(f'old code={old_len:,}  new code={len(code):,}  delta={delta:+d}')
    print(f'new blob={len(blob):,} (old {layout["blob"]["size"]:,}, delta={len(blob)-layout["blob"]["size"]:+d})')
    print(f'-> {out_bin}')

if __name__ == '__main__':
    main()
