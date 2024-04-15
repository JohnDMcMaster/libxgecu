import binascii
import struct
import hexdump
import glob
from collections import namedtuple, OrderedDict


FILE_HEADER = struct.Struct("<BBHIII")
FileHeader = namedtuple('FileHeader', ['minor_version', 'major_version', 'magic', 'crc32',
                                       'pad','num_blocks'])
BLOCK = struct.Struct("<IIII 260s")
Block = namedtuple('Block', ['crc32', 'index', 'unknown', 'pad', 'data'])

def xorbytes(a, b):
    c = bytearray()
    for i in range(len(a)):
        c.append(a[i] ^ b[i])
    return c

def bitCount(int_type):
    count = 0
    while(int_type):
        int_type &= int_type - 1
        count += 1
    return(count)

def swiz(addr):
    return ((addr& 0x07070707) << 5) | ((addr & 0xf8f8f8f8) >>  3)

def unswiz(addr):
    return ((addr& 0xE0E0E0E0) >> 5) | ((addr & 0x1f1f1f1f) <<  3)

def xor_arrays(a,b):
    return bytes([ a[i] ^ b[i] for i in range(len(a))])
    
def blk_addr(i):
    return i * 0x100 + 0x08005000

def read_file(filename):
    with open(filename, "rb") as fil:
        filedata = fil.read()

        file_header = FileHeader(*FILE_HEADER.unpack(filedata[:FILE_HEADER.size]))

        blocks = OrderedDict()
        offset = FILE_HEADER.size
        for i in range(file_header.num_blocks):
            block = Block(*BLOCK.unpack(filedata[offset:offset + BLOCK.size]))
            blocks[i] = block
            offset += BLOCK.size
            
        fcrc = binascii.crc32(filedata[FILE_HEADER.size:]) ^ 0xffffffff

        if fcrc != file_header.crc32:
            raise ValueError( "File CRC32 mismatch" )

        return file_header, blocks


def write_file( filename, hdr, blocks ):
    with open(filename, "wb") as fil:
        filedata = bytearray( FILE_HEADER.size + len(blocks) * BLOCK.size )

        offset = FILE_HEADER.size
        for i, blk in enumerate(blocks):
            offset = FILE_HEADER.size + i * BLOCK.size
            filedata[offset:offset + BLOCK.size] = BLOCK.pack( *blk )
            
        crc32 = binascii.crc32(filedata[FILE_HEADER.size:]) ^ 0xffffffff
        
        hdr = FileHeader(
            hdr.minor_version, hdr.major_version, 
            hdr.magic, crc32, hdr.pad, len(blocks) )

        filedata[0:FILE_HEADER.size] = FILE_HEADER.pack( *hdr )
        
        fil.write(filedata)

def block_key_idx(seed):
    return ((seed>>8)+(seed & 0xff)) & 0xff

def get_l2_key(seed):
    return struct.pack("<I",swiz(seed))
    
def do_xorpad( data, key, kidx ):
    datad = bytearray(len(data) )
    key_sz = len(key)
    for i in range(len(data)):
        ki0 = ( i + kidx ) % key_sz
        datad[i] = key[ki0] ^ data[i]
    return datad
    
def do_xorfix( data, key ):
    # Decrypt static XOR layer
    datadf = bytearray(len(data))
    for i in range(0, len(data),4):
        # DeXOR
        datadf[i+0]  = key[0] ^ data[i+0]
        datadf[i+1]  = key[1] ^ data[i+1]
        datadf[i+2]  = key[2] ^ data[i+2]
        datadf[i+3]  = key[3] ^ data[i+3]     
    return datadf

def unswiz_data(data):
    datadf = bytearray(len(data))
    for i in range(0, len(data),4):
        # Unswiz
        d, = struct.unpack("<I",data[i:i+4])
        d = unswiz(d)        
        datadf[i:i+4] = struct.pack("<I",d)
    return datadf
    
def swiz_data(data):
    datadf = bytearray(len(data))
    for i in range(0, len(data),4):
        # Unswiz
        d, = struct.unpack("<I",data[i:i+4])
        d = swiz(d)       
        datadf[i:i+4] = struct.pack("<I",d)
    return datadf

def decr_blk(blk):
    
    # Get the start key index
    kidx = block_key_idx(blk.index)
    
    # Compute the key
    swidx = swiz( blk.index )
    hk = struct.pack("<I",swidx)
    
    # Decrypt XOR pad layer
    dxdata = do_xorpad( blk.data, key, kidx )
    
    # Decrypt static XOR layer
    dsdata = do_xorfix( dxdata, hk )
    
    # Unswizzle the data
    datadf = unswiz_data( dsdata )
    
    # Verify the checksum
    if blk.crc32  != (binascii.crc32(datadf) ^ 0xffffffff):
        raise ValueError("Block checksum mismatch")
        
    return datadf   

def encr_blk( data, index, unknown, pad ):
    
    # Get the start key index
    kidx = block_key_idx( index )
    
    # Compute the key
    swidx = swiz( index )
    hk = struct.pack("<I",swidx)
    
    # Swizzle the data
    datadf = swiz_data( data )
    
    # Encrypt static XOR layer
    dsdata = do_xorfix( datadf, hk )
    
    # Encrypt XOR pad layer 
    dxdata = do_xorpad( dsdata, key, kidx )
    
    # Compute the checksum
    crc32 = binascii.crc32(data) ^ 0xffffffff
    
    return Block( crc32, index, unknown, pad, dxdata )

with open("key.dat","rb") as kf:
    key = kf.read(516)
    
   
    