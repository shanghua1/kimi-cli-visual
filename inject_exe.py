# -*- coding: utf-8 -*-
"""把重建好的 blob 注入 exe（postject 封装；PE 资源重建交给它，支持扩容）。
用法: python inject_exe.py <blob.bin> <out.exe> [base_exe]
  base_exe 默认 pristine 备份 kimi.exe.bak-0.28.1（永远在干净底子上注入，幂等可重跑）。
注入后自验：重新解析 PE，确认资源 size == 新 blob size，且 blob 头 main_len 与 code 吻合。"""
import json, os, shutil, subprocess, sys
from sea_pe import walk_resources, find_sea_blob, parse_blob_header

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BASE = os.path.expanduser(r'~/.kimi-code/bin/kimi.exe.bak-0.28.1')
FUSE = 'NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2'

def main():
    blob_bin, out_exe = sys.argv[1], sys.argv[2]
    base = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_BASE
    blob = open(blob_bin, 'rb').read()

    shutil.copyfile(base, out_exe)
    npx = shutil.which('npx') or shutil.which('npx.cmd') or 'npx'
    cmd = [npx, '--no-install', 'postject', out_exe, 'NODE_SEA_BLOB', blob_bin,
           '--sentinel-fuse', FUSE, '--overwrite']
    print('+', ' '.join(cmd))
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr)
        print('FATAL: postject 注入失败')
        sys.exit(1)

    # 自验
    data = open(out_exe, 'rb').read()
    pe, rsrc, resources = walk_resources(data)
    b = find_sea_blob(resources)
    ok_size = b['size'] == len(blob)
    h = parse_blob_header(data[b['file_off']:b['file_off'] + b['size']])
    ok_len = h['main_len'] == len(blob) - h['header_len'] - json.load(
        open(os.path.join(HERE, 'work', 'layout.json')))['tail_len']
    ok_head = data[b['file_off']:b['file_off'] + b['size']] == blob
    print(f'verify: resource_size={b["size"]:,} (expect {len(blob):,}) -> {"OK" if ok_size else "MISMATCH"}')
    print(f'verify: header main_len={h["main_len"]:,} -> {"OK" if ok_len else "MISMATCH"}')
    print(f'verify: blob bytes identical -> {"OK" if ok_head else "MISMATCH"}')
    if not (ok_size and ok_len and ok_head):
        print('FATAL: 注入自验失败')
        sys.exit(1)
    print(f'-> {out_exe} ({len(data):,} bytes)')

if __name__ == '__main__':
    main()
