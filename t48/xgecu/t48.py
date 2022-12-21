import binascii
import time
import usb1
# from usbrply.util import hexdump

def validate_read(expected, actual, msg):
    if expected != actual:
        print('Failed %s' % msg)
        print('  Expected; %s' % binascii.hexlify(expected,))
        print('  Actual:   %s' % binascii.hexlify(actual,))
        #raise Exception('failed validate: %s' % msg)

class T48:
    def __init__(self, usbcontext, dev, init=True):
        self.usbcontext = usbcontext
        self.dev = dev

        # does not seem to be required for version init
        if 0 and init:
            # XXX: send this at init only or just before version read?
            buff = self.controlRead(0xC0, 0xEE, 0x0000, 0x0004, 16)
            validate_read(b"\x28\x00\x00\x00\x00\x01\x04\x00\x01\x00\x00\x00\x00\x00\x00\x00", buff, "packet 1088/1089")

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

    def version_raw(self):
        self.bulkWrite(0x01, b"\x00\x00\x00\x00\x00\x00\x00\x00")
        buff = self.bulkRead(0x81, 0x0200)
        old = (b"\x00\x01\x30\x00\x03\x01\x07\x00\x32\x30\x32\x32\x2D\x30\x39\x2D"
                b"\x32\x31\x30\x39\x3A\x32\x37\x00\x32\x39\x41\x30\x33\x36\x33\x32"
                b"\x57\x44\x4E\x35\x59\x46\x4F\x4D\x4B\x32\x52\x52\x56\x4A\x30\x41"
                b"\x32\x46\x39\x53\x39\x36\x31\x33\x1F\x06\x00\x00\x01\x00\x00")
        assert len(buff) == len(old)
        return buff

    def test1(self):
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

    def reset(self):
        self.bulkWrite(0x01, b"\x3F\x00\x00\x00\x00\x00\x00\x00")

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
    raise Exception("Failed to find a device")

def get():
    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    dev.claimInterface(0)
    dev.resetDevice()
    return T48(usbcontext=usbcontext, dev=dev)
