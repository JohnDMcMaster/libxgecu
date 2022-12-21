#!/usr/bin/env python3

from xgecu import t48
import time
import usb1

def main():
    import argparse 

    parser = argparse.ArgumentParser(description="Reset programmer")
    args = parser.parse_args()

    t = t48.get()
    t.reset()

    # 1.4 sec
    tstart = time.time()
    while True:
        try:
            t = t48.get()
            break
        except t48.DeviceNotFound:
            pass
        except usb1.USBErrorBusy:
            pass
        time.sleep(0.05)
    dt = time.time() - tstart
    print("Found after %0.1f sec" % dt)


if __name__ == "__main__":
    main()
