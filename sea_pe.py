# -*- coding: utf-8 -*-
"""kimi-beautify 共享库：PE/.rsrc 解析 + SEA blob 头解析。

经验布局（v0.28.1 实测，两个独立侦查报告一致）：
  blob[0:4]   u32  = 21,223,968（assets 区长度）
  blob[4:8]   u32  = 9
  blob[8]     u8   = 1（flags: bit0 useSnapshot=1, bit1 useCodeCache=0）
  blob[9:17]  u64  = code_path 长度（74）
  blob[17:91]      = code_path 字节
  blob[91:99] u64  = main_len  ← 重建时唯一需要改的头字段
  blob[99:…]       = JS code，随后是 assets 区 + 末尾清单 JSON
"""
import struct

def parse_pe(data):
    e_lfanew = struct.unpack('<I', data[0x3C:0x40])[0]
    assert data[e_lfanew:e_lfanew+4] == b'PE\x00\x00', 'not a PE file'
    coff = e_lfanew + 4
    num_sections = struct.unpack('<H', data[coff+2:coff+4])[0]
    size_opt = struct.unpack('<H', data[coff+16:coff+18])[0]
    opt = coff + 20
    opt_magic = struct.unpack('<H', data[opt:opt+2])[0]
    assert opt_magic == 0x20B, 'expected PE32+'
    sec_base = opt + size_opt
    sections = []
    for i in range(num_sections):
        s = sec_base + i * 40
        name = data[s:s+8].rstrip(b'\x00').decode('ascii', 'replace')
        vsize, vaddr, raw_size, raw_off = struct.unpack('<IIII', data[s+8:s+24])
        sections.append({'name': name, 'vaddr': vaddr, 'vsize': vsize,
                         'raw_size': raw_size, 'raw_off': raw_off, 'hdr_off': s})
    # PE32+ data directories 起点 = opt+112；index 2 = Resource Table（RVA+Size 各 u32）
    dd_rsrc_off = opt + 112 + 2 * 8
    return {'opt': opt, 'sections': sections, 'dd_rsrc_off': dd_rsrc_off}

def walk_resources(data):
    """返回 (pe, rsrc_section, resources[])。resources 每项含 file_off/size/entry_off（数据目录项的文件偏移，+4 即 size 字段）。"""
    pe = parse_pe(data)
    rsrc = next(s for s in pe['sections'] if s['name'] == '.rsrc')
    R0, V0 = rsrc['raw_off'], rsrc['vaddr']

    def u16(o): return struct.unpack('<H', data[o:o+2])[0]
    def u32(o): return struct.unpack('<I', data[o:o+4])[0]

    def res_name(o, named):
        if not named:
            return o
        no = R0 + (o & 0x7FFFFFFF)
        ln = u16(no)
        return data[no+2:no+2+ln*2].decode('utf-16le', 'replace')

    resources = []

    def walk(dir_off, names):
        base = R0 + dir_off
        total = u16(base+12) + u16(base+14)
        for i in range(total):
            e = base + 16 + i * 8
            name_raw, val_raw = u32(e), u32(e+4)
            nm = res_name(name_raw, bool(name_raw & 0x80000000))
            if val_raw & 0x80000000:
                walk(val_raw & 0x7FFFFFFF, names + [nm])
            else:
                de = R0 + val_raw
                rva, sz = u32(de), u32(de+4)
                resources.append({'path': names + [nm], 'rva': rva, 'size': sz,
                                  'file_off': R0 + (rva - V0), 'entry_off': de})
    walk(0, [])
    return pe, rsrc, resources

def find_sea_blob(resources):
    """最大的资源即 NODE_SEA_BLOB。"""
    return max(resources, key=lambda r: r['size'])

def parse_blob_header(blob):
    field0, version = struct.unpack('<II', blob[0:8])
    flags = blob[8]
    o = 9
    cp_len = struct.unpack('<Q', blob[o:o+8])[0]; o += 8
    code_path = blob[o:o+cp_len].decode('utf-8', 'replace'); o += cp_len
    main_len = struct.unpack('<Q', blob[o:o+8])[0]; o += 8
    return {'field0': field0, 'version': version, 'flags': flags,
            'code_path': code_path, 'main_len': main_len, 'header_len': o}

def build_blob_header(h, new_main_len):
    out = struct.pack('<II', h['field0'], h['version']) + bytes([h['flags']])
    path = h['code_path'].encode('utf-8')
    out += struct.pack('<Q', len(path)) + path
    out += struct.pack('<Q', new_main_len)
    assert len(out) == h['header_len'], f'header length drift: {len(out)} != {h["header_len"]}'
    return out
