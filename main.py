"""
Command-line interface for the Huffman compressor.

Usage:
  python main.py compress   sample.txt            -> sample.txt.huff
  python main.py decompress sample.txt.huff       -> sample.txt.out
  python main.py demo       sample.txt            -> full walkthrough
"""

import argparse
import os
import time

import huffman as hf


def show_code_table(data: bytes, limit: int = 15):
    freq = hf.build_frequency_table(data)
    codes = hf.generate_codes(hf.build_tree(freq))
    rows = sorted(freq.items(), key=lambda kv: -kv[1])[:limit]

    print(f"\nTop {len(rows)} symbols (of {len(freq)} distinct):")
    print(f"{'Char':<8}{'Freq':>8}  {'Code':<16}{'Bits':>5}")
    print("-" * 40)
    for sym, f in rows:
        ch = repr(chr(sym)) if 32 <= sym < 127 else f"0x{sym:02x}"
        print(f"{ch:<8}{f:>8}  {codes[sym]:<16}{len(codes[sym]):>5}")


def print_stats(stats: dict):
    print(f"Original size   : {stats['original_bytes']:,} bytes")
    print(f"Compressed size : {stats['compressed_bytes']:,} bytes")
    print(f"Ratio           : {stats['ratio']:.3f}")
    print(f"Space saved     : {stats['saved_percent']:.1f}%")


def cmd_compress(args):
    out = args.output or args.input + ".huff"
    print_stats(hf.compress_file(args.input, out))
    print(f"Saved -> {out}")


def cmd_decompress(args):
    out = args.output or (
        args.input[:-5] if args.input.endswith(".huff") else args.input
    ) + ".out"
    n = hf.decompress_file(args.input, out)
    print(f"Restored {n:,} bytes -> {out}")


def cmd_demo(args):
    with open(args.input, "rb") as f:
        data = f.read()

    print(f"File: {args.input}")
    show_code_table(data)

    t0 = time.perf_counter()
    blob = hf.compress(data)
    t1 = time.perf_counter()
    restored = hf.decompress(blob)
    t2 = time.perf_counter()

    print("\n--- Result ---")
    print_stats(hf.compression_stats(len(data), len(blob)))
    print(f"Compress time   : {(t1 - t0) * 1000:.2f} ms")
    print(f"Decompress time : {(t2 - t1) * 1000:.2f} ms")
    print(f"Lossless check  : {'PASSED' if restored == data else 'FAILED'}")


def cmd_web(args):
    from web_app import serve

    serve(args.host, args.port)


def main():
    p = argparse.ArgumentParser(description="Huffman Coding file compressor")
    sub = p.add_subparsers(dest="command", required=True)

    for name, fn, help_ in [
        ("compress", cmd_compress, "compress a file"),
        ("decompress", cmd_decompress, "decompress a .huff file"),
        ("demo", cmd_demo, "show codes, sizes, timing and verify"),
    ]:
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("input")
        if name != "demo":
            sp.add_argument("-o", "--output")
        sp.set_defaults(func=fn)

    web = sub.add_parser("web", help="start the browser-based app")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8000)
    web.set_defaults(func=cmd_web)

    args = p.parse_args()
    if args.command != "web" and not os.path.isfile(args.input):
        p.error(f"file not found: {args.input}")
    args.func(args)


if __name__ == "__main__":
    main()
