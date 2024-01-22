import t48crypto as t48
import sys
import struct

def print_hdr( file, hdr ):
    print( "HEADER Major=0x%02X Minor=0x%02X Magic=0x%04X Pad=0x%08X"%(
        hdr.major_version,hdr.minor_version,hdr.magic,hdr.pad), file=file )

def print_blk( file, blk, offset ):
    print( "BLOCK Seed=0x%08X Unk=0x%08X Pad=0x%08X Offset=0x%08X"%(
            blk.index, blk.unknown, blk.pad, offset), file=file )

file_in = sys.argv[1]
file_out = sys.argv[2]

bin_out = file_out + ".bin"
txt_out = file_out + ".txt"

hdr, blocks = t48.read_file( file_in )

flash_base = 0x08000000

with open(txt_out,"w") as txtf:
    with open(bin_out, "wb") as binf:
        print_hdr( txtf, hdr )
        for i in blocks:
            blk = blocks[i]
            data = t48.decr_blk( blk )
            offset, payl = struct.unpack("<I 256s", data)
            print_blk( txtf, blk, offset )
            file_offset = offset - flash_base
            binf.seek( file_offset )
            binf.write( payl )

