import t48crypto as t48
import sys
import struct

def print_hdr( file, hdr ):
    print( "HEADER Major=0x%02X Minor=0x%02X Magic=0x%04X Pad=0x%08X"%(
        hdr.major_version,hdr.minor_version,hdr.magic,hdr.pad), file=file )

def parse_line( l ):
    l = l.strip()
    if len(l) == 0 or l[0] == '#':
        return None
    parts = l.split(" ")
    what = parts[0]
    parts = parts[1:]
    kvs = {}
    for p in parts:
        k,v = p.split("=")
        v = int(v,0)
        kvs[k] = v
    return what, kvs
        

def print_blk( file, blk, offset ):
    print( "BLOCK Seed=0x%08X Unk=0x%08X Pad=0x%08X Offset=0x%08X"%(
            blk.index, blk.unknown, blk.pad, offset), file=file )

file_in = sys.argv[1]

bin_in = file_in + ".bin"
txt_in = file_in + ".txt"
enc_out = file_in + ".dat"

flash_base = 0x08000000

hdr = None
blocks = []
with open(txt_in, "r") as txtf:
    with open(bin_in, "rb") as binf:
        for l in txtf:
            a = parse_line(l)
            if a is None:
                continue
            what,kv = a
            if what == "HEADER":
                hdr = t48.FileHeader(kv["Minor"],kv["Major"],kv["Magic"],0,kv["Pad"],0)
            elif what == "BLOCK":
                offset = kv["Offset"]
                file_offset = offset - flash_base
                binf.seek( file_offset )
                payl = binf.read( 256 )
                data = struct.pack( "<I 256s", offset, payl )
                blk = t48.encr_blk( data, kv["Seed"], kv["Unk"], kv["Pad"] )
                blocks.append(blk)
                
t48.write_file( enc_out, hdr, blocks )
