# -*- coding: utf-8 -*-
"""从干净的 kimi.exe 提取 SEA blob：header / main.cjs / tail（assets+清单）。
用法: python extract_blob.py [kimi.exe 路径]
默认源: ~/.kimi-code/bin/kimi.exe.bak-0.28.1（本版 pristine 备份）
产物: work/header.bin work/main.orig.cjs work/tail.bin work/layout.json
幂等: 重复运行覆盖同一产物。"""
import json, os, sys
from sea_pe import walk_resources, find_sea_blob, parse_blob_header

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'work')
DEFAULT_EXE = os.path.expanduser(r'~/.kimi-code/bin/kimi.exe.bak-0.28.1')

def main():
    exe = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EXE
    print(f'source exe: {exe} ({os.path.getsize(exe):,} bytes)')
    data = open(exe, 'rb').read()
    pe, rsrc, resources = walk_resources(data)
    blob = find_sea_blob(resources)
    print(f"SEA blob resource: path={blob['path']} file_off={blob['file_off']:,} size={blob['size']:,}")
    # 重叠体检：blob 之后是否还有其他资源（扩容安全性前置确认）
    after = [r for r in resources if r is not blob and r['file_off'] >= blob['file_off']]
    slack = rsrc['raw_off'] + rsrc['raw_size'] - (blob['file_off'] + blob['size'])
    print(f'.rsrc slack after blob: {slack:,} bytes; resources at/after blob: {len(after)}')
    for r in after:
        print(f"  !! resource after blob: {r['path']} off={r['file_off']:,} size={r['size']:,}")

    raw = data[blob['file_off']:blob['file_off'] + blob['size']]
    h = parse_blob_header(raw)
    print(f"header: field0={h['field0']:,} version={h['version']} flags=0x{h['flags']:02x} "
          f"main_len={h['main_len']:,} header_len={h['header_len']}")
    print(f"code_path: {h['code_path']!r}")
    code = raw[h['header_len']:h['header_len'] + h['main_len']]
    tail = raw[h['header_len'] + h['main_len']:]
    assert code.startswith(b'#!') or code[:20].strip(), 'code head looks wrong'
    print(f"code: {len(code):,} bytes; tail: {len(tail):,} bytes")

    os.makedirs(WORK, exist_ok=True)
    open(os.path.join(WORK, 'header.bin'), 'wb').write(raw[:h['header_len']])
    open(os.path.join(WORK, 'main.orig.cjs'), 'wb').write(code)
    open(os.path.join(WORK, 'tail.bin'), 'wb').write(tail)
    layout = {'exe': exe, 'blob': {k: (v if not isinstance(v, list) else [str(x) for x in v])
                                  for k, v in blob.items()},
              'header': h, 'tail_len': len(tail), 'slack_after_blob': slack,
              'rsrc': {k: v for k, v in rsrc.items()}}
    json.dump(layout, open(os.path.join(WORK, 'layout.json'), 'w'), indent=2)
    print(f'-> {WORK}: header.bin({h["header_len"]}) main.orig.cjs({len(code):,}) '
          f'tail.bin({len(tail):,}) layout.json')

if __name__ == '__main__':
    main()
