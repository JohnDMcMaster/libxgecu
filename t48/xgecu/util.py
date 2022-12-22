import sys
import struct

def hexdump(data, label=None, indent='', address_width=8, f=sys.stdout):
    def isprint(c):
        return c >= ' ' and c <= '~'

    if label:
        print(label)

    bytes_per_half_row = 8
    bytes_per_row = 16
    data = bytearray(data)
    data_len = len(data)

    def hexdump_half_row(start):
        left = max(data_len - start, 0)

        real_data = min(bytes_per_half_row, left)

        f.write(''.join('%02X ' % c for c in data[start:start + real_data]))
        f.write(''.join('   ' * (bytes_per_half_row - real_data)))
        f.write(' ')

        return start + bytes_per_half_row

    pos = 0
    while pos < data_len:
        row_start = pos
        f.write(indent)
        if address_width:
            f.write(('%%0%dX  ' % address_width) % pos)
        pos = hexdump_half_row(pos)
        pos = hexdump_half_row(pos)
        f.write("|")
        # Char view
        left = data_len - row_start
        real_data = min(bytes_per_row, left)

        f.write(''.join([
            c if isprint(c) else '.'
            for c in tostr(data[row_start:row_start + real_data])
        ]))
        f.write((" " * (bytes_per_row - real_data)) + "|\n")


def add_bool_arg(parser, yes_arg, default=False, **kwargs):
    dashed = yes_arg.replace('--', '')
    dest = dashed.replace('-', '_')
    parser.add_argument(yes_arg,
                        dest=dest,
                        action='store_true',
                        default=default,
                        **kwargs)
    kwargs['help'] = 'Disable above'
    parser.add_argument('--no-' + dashed,
                        dest=dest,
                        action='store_false',
                        **kwargs)

def tobytes(buff):
    if type(buff) is str:
        #return bytearray(buff, 'ascii')
        return bytearray([c for c in buff])
    elif type(buff) is bytearray or type(buff) is bytes:
        return buff
    else:
        assert 0, type(buff)


def tostr(buff):
    if type(buff) is str:
        return buff
    elif type(buff) is bytearray or type(buff) is bytes:
        return ''.join([chr(b) for b in buff])
    else:
        assert 0, type(buff)


def isprint(c):
    return c >= ' ' and c <= '~'

class StructStreamer:
    def __init__(self, buf, verbose=False):
        self.buf = bytearray(buf)
        self.len = len(self.buf)
        self.d = {}
        self.verbose = verbose

    def done(self):
        assert len(self.buf) == 0
        return self.d

    def popped(self):
        """Number of bytes consumed so far"""
        return self.len - len(self.buf)

    def pop_n(self, n):
        self.verbose and hexdump(self.buf, "pop %u" % n)
        assert len(self.buf) >= n, "Only %u bytes left, need %u" % (len(self.buf), n)
        v = self.buf[0:n]
        del self.buf[0:n]
        return v

    def assert_bytes(self, buf):
        got = self.pop_n(len(buf))
        assert got == buf

    def assert_str(self, want):
        got = self.pop_n(len(want))
        got = tostr(got)
        assert want == got, "Wanted %s got %s" % (want, got)

    def res(self, n, k=None):
        """
        Add n reserved / unknown bytes
        """
        if k is None:
            if self.len < 10:
                k = "res%01u" % self.popped()
            elif self.len < 100:
                k = "res%02u" % self.popped()
            else:
                k = "res%03u" % self.popped()
        v = self.pop_n(n)
        self.d[k] = v
        return v

    def strn(self, k, n):
        """
        pop string of exactly n characters
        """
        v = tostr(self.pop_n(n))
        self.d[k] = v
        return v

    def strn0(self, k, n):
        """
        pop string of exactly n characters, but truncate at first 0, if any
        """
        buf = self.pop_n(n)
        i = buf.find(0)
        if i >= 0:
            buf = buf[0:i]
        v = tostr(buf)
        self.d[k] = v
        return v

    def u32b(self, k):
        v = struct.unpack('>I', self.pop_n(4))[0]
        self.d[k] = v
        return v

    def u32l(self, k):
        v = struct.unpack('<I', self.pop_n(4))[0]
        self.d[k] = v
        del self.buf[0:4]
        return v
    
    def u16b(self, k):
        v = struct.unpack('>H', self.pop_n(2))[0]
        self.d[k] = v
        return v
    
    def u16l(self, k):
        v = struct.unpack('<H', self.pop_n(2))[0]
        self.d[k] = v
        return v

    def u8(self, k):
        v = self.buf[0]
        self.d[k] = v
        del self.buf[0:1]
        return v
