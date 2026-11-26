# File Compression Using Huffman Coding

**Course:** Design and Analysis of Algorithms (Capstone, Project 3)
**Language:** Python 3 (standard library only)

## Problem Statement
Reduce the storage needed for text files using Huffman Coding: calculate character frequencies, build a Huffman tree, generate binary codes, encode and decode, analyse time and space complexity, and compare original and compressed file sizes.

## Features
- Lossless compression and decompression of any file (works on raw bytes)
- Min-heap based tree construction (greedy algorithm)
- Prefix-free code table generation
- Compressed file stores a header (original length + frequency table) so the decoder can rebuild the identical tree
- CLI with `compress`, `decompress` and `demo` commands
- Local browser app with text/file compression, decompression, code table, size/timing analysis and algorithm overview
- 16 unit tests (empty file, single character, all 256 byte values, Unicode, prefix-free property, known optimal length and web API round-trips)
- Benchmark script with graph

## Project Structure
```
huffman.py         core algorithm (tree, codes, encode, decode, file I/O)
main.py            command-line interface
web_app.py         local HTTP server and compression API
web/               browser interface (HTML, CSS and JavaScript)
benchmark.py       timing and compression analysis on different input sizes
test_huffman.py    unit tests
test_web_app.py    web response and round-trip tests
sample.txt         sample input
benchmark.png      generated graph
```

## How to Run
```bash
python main.py demo sample.txt          # codes, sizes, timing, verification
python main.py compress sample.txt      # creates sample.txt.huff
python main.py decompress sample.txt.huff   # creates sample.txt.out
python main.py web                           # open http://127.0.0.1:8000
python -m unittest -v                   # run tests
python benchmark.py                     # performance analysis (pip install matplotlib for graph)
```

The web app uses only Python's standard library and runs locally. Choose **Text** or **File** to compress input, then download the resulting `.huff` file; choose a `.huff` file in the restore section to decompress it. The app displays the complete byte-symbol code table and compression statistics. Files up to 25 MiB are supported.

## Algorithm
1. **Count frequencies** of every byte in the input.
2. **Put each byte in a min-heap** keyed by frequency.
3. **Repeat:** remove the two smallest nodes, create a parent with the sum of their frequencies, push it back.
4. The last node left is the **root**. Walk the tree: left edge = `0`, right edge = `1`. The path to a leaf is that byte's code.
5. **Encode:** replace each byte by its code and pack the bits into bytes.
6. **Decode:** start at the root, follow bits to a leaf, output the byte, return to the root.

Why it is correct: it is a greedy algorithm. Always merging the two least frequent nodes produces an optimal prefix code (minimum total encoded length). Codes are prefix-free, so no separators are needed.

## Complexity Analysis
Let `n` = input size in bytes, `k` = number of distinct bytes (`k <= 256`).

| Phase | Time | Reason |
|---|---|---|
| Frequency count | O(n) | one pass over the data |
| Build tree | O(k log k) | k-1 merges, each heap op is O(log k) |
| Generate codes | O(k) | visit each tree node once |
| Encode | O(n) | one dictionary lookup per byte |
| Decode | O(n) | at most one tree step per bit |
| **Total** | **O(n + k log k)** | effectively **O(n)** since k is at most 256 |

**Space:** O(k) for the tree and code table, plus O(n) for the bit string and output.

## Results
Random English-like text (skewed letter frequencies), measured by `benchmark.py`:

| Input (bytes) | Compressed (bytes) | Space saved | Compress (ms) | Decompress (ms) |
|---:|---:|---:|---:|---:|
| 1,000 | 859 | 14.1% | 0.6 | 1.0 |
| 10,000 | 5,738 | 42.6% | 3.6 | 7.3 |
| 100,000 | 54,162 | 45.8% | 36.5 | 62.4 |
| 500,000 | 268,988 | 46.2% | 85.7 | 213.9 |
| 1,000,000 | 537,660 | 46.2% | 168.9 | 435.2 |

`sample.txt` (1,611 bytes of English prose): compressed to 1,455 bytes, **9.7% saved**.

### Observations
- **Time grows roughly linearly** with input size, matching the O(n) analysis.
- **Compression improves with size** and levels off near 46% for this text. For small files the header (frequency table, stored as JSON) is a large share of the output, which is why `sample.txt` saves only 9.7%.
- Compression works best when the character distribution is **skewed**. Data with nearly uniform byte frequencies (already compressed or random data) will not shrink, and can grow slightly because of the header.
- Decompression is slower than compression in this implementation because decoding walks the tree bit by bit in Python.

## Limitations and Possible Improvements
- Store the header more compactly (binary instead of JSON, or a canonical Huffman code table) to help small files.
- Speed up decoding with lookup tables instead of a bit-by-bit tree walk.
- Process large files in chunks instead of loading them fully into memory.
- Adaptive Huffman coding for streaming data.
