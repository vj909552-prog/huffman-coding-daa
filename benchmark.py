"""
Benchmark: how do time and compression ratio change with input size?

Run:  python benchmark.py
(If matplotlib is installed it also saves benchmark.png)
"""

import random
import string
import time

import huffman as hf

SIZES = [1_000, 10_000, 100_000, 500_000, 1_000_000]
random.seed(42)

# Skewed letter weights, like real English text (space and 'e' are common).
ALPHABET = string.ascii_lowercase + " "
WEIGHTS = [8, 2, 3, 4, 12, 2, 2, 6, 7, 1, 1, 4, 2, 7, 8, 2, 1, 6, 6, 9, 3, 1, 2, 1, 2, 1, 18]


def make_text(n):
    return "".join(random.choices(ALPHABET, WEIGHTS, k=n)).encode()


def timed(fn, *a):
    t = time.perf_counter()
    result = fn(*a)
    return result, (time.perf_counter() - t) * 1000


def main():
    print(f"{'Size (B)':>10} {'Compressed':>11} {'Saved %':>8} {'Comp ms':>9} {'Decomp ms':>10} {'OK':>4}")
    print("-" * 58)

    results = []
    for n in SIZES:
        data = make_text(n)
        blob, t_c = timed(hf.compress, data)
        restored, t_d = timed(hf.decompress, blob)
        s = hf.compression_stats(len(data), len(blob))
        ok = restored == data
        results.append((n, s["saved_percent"], t_c, t_d))
        print(f"{n:>10,} {len(blob):>11,} {s['saved_percent']:>8.1f} {t_c:>9.1f} {t_d:>10.1f} {'yes' if ok else 'NO':>4}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n(matplotlib not installed - skipping graph. pip install matplotlib)")
        return

    xs = [r[0] for r in results]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
    a1.plot(xs, [r[2] for r in results], "o-", label="compress")
    a1.plot(xs, [r[3] for r in results], "s-", label="decompress")
    a1.set_xlabel("Input size (bytes)")
    a1.set_ylabel("Time (ms)")
    a1.set_title("Running time vs input size (~linear)")
    a1.legend()
    a1.grid(alpha=0.3)

    a2.plot(xs, [r[1] for r in results], "o-", color="green")
    a2.set_xscale("log")
    a2.set_xlabel("Input size (bytes, log scale)")
    a2.set_ylabel("Space saved (%)")
    a2.set_title("Compression vs input size")
    a2.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig("benchmark.png", dpi=120)
    print("\nSaved graph -> benchmark.png")


if __name__ == "__main__":
    main()
