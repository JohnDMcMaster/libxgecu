#!/usr/bin/env python3

from xgecu import t48
from xgecu.util import hexdump

def main():
    import argparse 

    parser = argparse.ArgumentParser(description="Version info")
    parser.add_argument("--fn-in", help="Parse file instead of running live")
    parser.add_argument("fn_out", nargs="?", help="Output file name")
    args = parser.parse_args()

    if args.fn_in:
        raw = open(args.fn_in, "rb").read()
        print("Read %u bytes from %s" % (len(raw), args.fn_in))
    else:
        t = t48.get()
        raw = t.version_raw()
        print("Read %u bytes from USB" % (len(raw),))
    hexdump(raw)
    if args.fn_out:
        open(args.fn, "wb").write(raw)
    print("")
    version = t48.parse_version(raw, verbose=0)
    print("model: %s" % version["model"])
    print("Dev code: %s" % version["dev_code"])
    print("Serial: %s" % version["serial"])
    print("FW version: %u.%u" % (version["ver_major"], version["ver_minor"]))
    print("Manufacture date: %s" % version["date"])

    hexdump(version["res00"], indent="res00: ")
    hexdump(version["res56"], indent="res56: ")


if __name__ == "__main__":
    main()
