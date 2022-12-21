#!/usr/bin/env python3

from xgecu import t48
from xgecu.util import hexdump
import argparse

def main():
    import argparse 

    parser = argparse.ArgumentParser(description="Version info")
    parser.add_argument("fn", nargs="?", help="Output file name")
    args = parser.parse_args()

    t = t48.get()
    raw = t.version_raw()
    # hexdump(t.test1())
    hexdump(raw)
    if args.fn:
        open(args.fn, "wb").write(raw)

if __name__ == "__main__":
    main()
