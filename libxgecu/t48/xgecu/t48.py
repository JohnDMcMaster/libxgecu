import binascii
import time
import usb1
import struct
from .util import StructStreamer
# from usbrply.util import hexdump

model_i2s = {
    6: "t56",
    7: "t48",
    }

class DeviceNotFound(Exception):
    pass

def validate_read(expected, actual, msg):
    if expected != actual:
        print('Failed %s' % msg)
        print('  Expected; %s' % binascii.hexlify(expected,))
        print('  Actual:   %s' % binascii.hexlify(actual,))
        #raise Exception('failed validate: %s' % msg)


def parse_version(buf, decode=True, verbose=False):
    """Return best effort decoded version info as dict"""
    assert len(buf) == 63 or len(buf) == 64
    """
    Sample T48
    00000000  00 01 30 00 07 01 07 00  32 30 32 32 2D 30 39 2D  |..0.....2022-09-|
    00000010  32 31 30 39 3A 32 37 00  32 39 41 30 33 36 33 32  |2109:27.29A03632|
    00000020  57 44 4E 35 59 46 4F 4D  4B 32 52 52 56 4A 30 41  |WDN5YFOMK2RRVJ0A|
    00000030  32 46 39 53 39 36 31 33  1B 06 00 00 01 00 00     |2F9S9613....... |
    """
    ss = StructStreamer(buf, verbose=verbose)
    # always 00 01 30 00
    # magic number?
    ss.res(4)
    # ex: 37 01 => version 1.55
    # ex: 41 01 => version 1.65
    ss.u8("ver_minor")
    ss.u8("ver_major")
    # There are several bytes that correlate with model
    # Assume this for now
    # ex: 07 00 => T48
    # ex: 08 00 => T56
    ss.u16l("model")
    """
    pop 13
    00000000  32 32 2D 30 36 2D 32 38  32 33 3A 34 30 00 32 36  |22-06-2823:40.26|
    00000010  42 30 31 33 33 36 39 57  50 4B 42 49 35 38 39 36  |B013369WPKBI5896|

    pop 13
    00000000  32 31 2D 31 30 2D 30 38  20 30 30 3A 33 37 31 33  |21-10-08 00:3713|
    00000010  32 30 31 30 37 39 30 39  33 4C 57 39 52 56 36 4B  |201079093LW9RV6K|
    """
    ss.strn0("date", 16)
    # GUI splits this into "DEV Code" + "Serial"
    ss.strn("dev_code", 8)
    ss.strn("serial", 24)
    """
    T48
    0A 06 00 00 01 00 00
    1B 06 00 00 01 00 00

    T56
    F3 05 00 00 01 00 00
    """
    ss.res(7)

    # T56 has an extra 0 byte at the end, shrug
    if ss.d["model"] == 6:
        ss.assert_str("\x00")

    ret = ss.done()
    if decode:
        ret["model"] = model_i2s[ret["model"]]
    return ret


class T48:
    def __init__(self, usbcontext, dev):
        self.usbcontext = usbcontext
        self.dev = dev

    def bulkRead(self, endpoint, length, timeout=None):
        return self.dev.bulkRead(endpoint, length, timeout=(1000 if timeout is None else timeout))

    def bulkWrite(self, endpoint, data, timeout=None):
        self.dev.bulkWrite(endpoint, data, timeout=(1000 if timeout is None else timeout))
    
    def controlRead(self, bRequestType, bRequest, wValue, wIndex, wLength,
                    timeout=None):
        return self.dev.controlRead(bRequestType, bRequest, wValue, wIndex, wLength,
                    timeout=(1000 if timeout is None else timeout))

    def controlWrite(self, bRequestType, bRequest, wValue, wIndex, data,
                     timeout=None):
        self.dev.controlWrite(bRequestType, bRequest, wValue, wIndex, data,
                     timeout=(1000 if timeout is None else timeout))

    def interruptRead(self, endpoint, size, timeout=None):
        return self.dev.interruptRead(endpoint, size,
                    timeout=(1000 if timeout is None else timeout))

    def interruptWrite(self, endpoint, data, timeout=None):
        self.dev.interruptWrite(endpoint, data, timeout=(1000 if timeout is None else timeout))

    def version_raw(self, check_size=True):
        """
        Can request more but won't get more bytes

        00000000  00 01 30 00 07 01 07 00  32 30 32 32 2D 30 39 2D  |..0.....2022-09-|
        00000010  32 31 30 39 3A 32 37 00  32 39 41 30 33 36 33 32  |2109:27.29A03632|
        00000020  57 44 4E 35 59 46 4F 4D  4B 32 52 52 56 4A 30 41  |WDN5YFOMK2RRVJ0A|
        00000030  32 46 39 53 39 36 31 33  1B 06 00 00 01 00 00     |2F9S9613....... |
        """
        self.bulkWrite(0x01, b"\x00\x00\x00\x00\x00\x00\x00\x00")
        buff = self.bulkRead(0x81, 0x0200)
        old = (b"\x00\x01\x30\x00\x03\x01\x07\x00\x32\x30\x32\x32\x2D\x30\x39\x2D"
                b"\x32\x31\x30\x39\x3A\x32\x37\x00\x32\x39\x41\x30\x33\x36\x33\x32"
                b"\x57\x44\x4E\x35\x59\x46\x4F\x4D\x4B\x32\x52\x52\x56\x4A\x30\x41"
                b"\x32\x46\x39\x53\x39\x36\x31\x33\x1F\x06\x00\x00\x01\x00\x00")
        # Appears T48 is 63 and T56 is 64
        assert not check_size or len(buff) == 63 or len(buff) == 64
        return buff


    def winusb_16(self):
        # Seems to be same as below, just fewer bytes verified
        buff = self.controlRead(0xC0, 0xEE, 0x0000, 0x0004, 16)
        validate_read(b"\x28\x00\x00\x00\x00\x01\x04\x00\x01\x00\x00\x00\x00\x00\x00\x00", buff, "packet 33/34")

    def winusb_40(self):
        """
        00000000  28 00 00 00 00 01 04 00  01 00 00 00 00 00 00 00  |(...............|
        00000010  00 01 57 49 4E 55 53 42  00 00 00 00 00 00 00 00  |..WINUSB........|
        00000020  00 00 00 00 00 00 00 00                           |........        |
        
        Can request more but won't get more bytes
        """
        buff = self.controlRead(0xC0, 0xEE, 0x0000, 0x0004, 40)
        ref = (b"\x28\x00\x00\x00\x00\x01\x04\x00\x01\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x01\x57\x49\x4E\x55\x53\x42\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00")
        assert len(buff) == len(ref)
        return buff

    def reset0_raw(self):
        self.bulkWrite(0x01, b"\x3F\x00\x00\x00\x00\x00\x00\x00")

    def reset2_raw(self):
        self.bulkWrite(0x01, b"\x3F\x02\x00\x01\x00\xFF\x03\x08")

    def reset(self, mode=0):
        """
        Reset and grab the new device / context after it comes back up
        """

        if mode == 0:
            self.reset0_raw()
        elif mode == 2:
            self.reset2_raw()
        else:
            assert 0, mode


        # 1.4 sec
        tstart = time.time()
        while True:
            try:
                t = get()
                break
            except DeviceNotFound:
                pass
            except usb1.USBErrorBusy:
                pass
            time.sleep(0.05)
        dt = time.time() - tstart
        # print("Found after %0.1f sec" % dt)

        # Shift in new device
        self.usbcontext = t.usbcontext
        self.dev = t.dev

def open_dev(usbcontext=None):
    vid_want = 0xA466
    pid_want = 0x0A53

    if usbcontext is None:
        usbcontext = usb1.USBContext()
    
    print('Scanning for devices...')
    for udev in usbcontext.getDeviceList(skip_on_error=True):
        vid = udev.getVendorID()
        pid = udev.getProductID()
        if (vid, pid) == (vid_want, pid_want):
            print('Found device')
            print('Bus %03i Device %03i: ID %04x:%04x' % (
                udev.getBusNumber(),
                udev.getDeviceAddress(),
                vid,
                pid))
            return udev.open()
    raise DeviceNotFound("Failed to find a device")

def get():
    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    dev.claimInterface(0)
    dev.resetDevice()
    return T48(usbcontext=usbcontext, dev=dev)
