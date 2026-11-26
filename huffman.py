"""
Huffman Coding - core algorithm.

Works on raw bytes, so it can compress any file (text, source code, etc.).

Steps:
  1. Count how often each byte occurs          -> build_frequency_table()
  2. Build the Huffman tree with a min-heap    -> build_tree()
  3. Walk the tree to get a binary code/byte   -> generate_codes()
  4. Replace each byte by its code, pack bits  -> encode() / compress()
  5. Walk the tree bit by bit to get data back -> decode() / decompress()

Complexity (n = input size in bytes, k = distinct bytes, k <= 256):
  Frequency count : O(n)
  Build tree      : O(k log k)
  Generate codes  : O(k)
  Encode          : O(n)
  Decode          : O(n)
  Total           : O(n + k log k)   -> effectively O(n) since k <= 256
  Space           : O(k) for the tree/codes, O(n) for the bit string/output
"""

import heapq
import json
import struct
from collections import Counter

MAGIC = b"HUFF"  # file signature so we can reject non-Huffman files


class Node:
    """A node of the Huffman tree. Leaves hold a symbol (byte value)."""

    __slots__ = ("symbol", "freq", "left", "right")

    def __init__(self, symbol, freq, left=None, right=None):
        self.symbol = symbol
        self.freq = freq
        self.left = left
        self.right = right

    def is_leaf(self):
        return self.left is None and self.right is None


# --------------------------------------------------------------------------
# Step 1: frequencies
# --------------------------------------------------------------------------
def build_frequency_table(data: bytes) -> dict:
    """Return {byte_value: count}."""
    return dict(Counter(data))


# --------------------------------------------------------------------------
# Step 2: tree
# --------------------------------------------------------------------------
def build_tree(freq: dict):
    """
    Build the Huffman tree from a frequency table.

    Heap entries are (freq, order, node). The `order` counter breaks ties so
    the tree is deterministic - the decompressor rebuilds the exact same tree
    from the stored frequency table.
    """
    if not freq:
        return None

    heap = [(f, i, Node(sym, f)) for i, (sym, f) in enumerate(sorted(freq.items()))]
    heapq.heapify(heap)
    order = len(heap)

    while len(heap) > 1:
        f1, _, left = heapq.heappop(heap)    # two smallest frequencies
        f2, _, right = heapq.heappop(heap)
        heapq.heappush(heap, (f1 + f2, order, Node(None, f1 + f2, left, right)))
        order += 1

    return heap[0][2]


# --------------------------------------------------------------------------
# Step 3: codes
# --------------------------------------------------------------------------
def generate_codes(root) -> dict:
    """Return {byte_value: '0101...'}. Left edge = '0', right edge = '1'."""
    if root is None:
        return {}
    if root.is_leaf():            # only one distinct byte in the file
        return {root.symbol: "0"}

    codes = {}
    stack = [(root, "")]
    while stack:
        node, path = stack.pop()
        if node.is_leaf():
            codes[node.symbol] = path
        else:
            stack.append((node.right, path + "1"))
            stack.append((node.left, path + "0"))
    return codes


# --------------------------------------------------------------------------
# Step 4: encoding
# --------------------------------------------------------------------------
def encode(data: bytes, codes: dict) -> str:
    """Convert data to a string of '0'/'1' characters."""
    return "".join(codes[b] for b in data)


def bits_to_bytes(bits: str) -> bytes:
    """Pack a bit string into bytes (zero-padded at the end)."""
    bits += "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def bytes_to_bits(data: bytes) -> str:
    return "".join(f"{b:08b}" for b in data)


# --------------------------------------------------------------------------
# Step 5: decoding
# --------------------------------------------------------------------------
def decode(bits: str, root, length: int) -> bytes:
    """Walk the tree bit by bit. `length` tells us when to stop (ignores padding)."""
    if length == 0 or root is None:
        return b""
    if root.is_leaf():
        return bytes([root.symbol]) * length

    out = bytearray()
    node = root
    for bit in bits:
        node = node.right if bit == "1" else node.left
        if node.is_leaf():
            out.append(node.symbol)
            if len(out) == length:
                break
            node = root
    return bytes(out)


# --------------------------------------------------------------------------
# Full compress / decompress (in memory)
# --------------------------------------------------------------------------
def compress(data: bytes) -> bytes:
    """
    File layout:
      4 bytes  magic 'HUFF'
      4 bytes  header length (big-endian)
      N bytes  header (JSON: original length + frequency table)
      rest     packed Huffman-coded bits
    """
    freq = build_frequency_table(data)
    root = build_tree(freq)
    codes = generate_codes(root)
    payload = bits_to_bytes(encode(data, codes))

    header = json.dumps(
        {"length": len(data), "freq": {str(k): v for k, v in freq.items()}}
    ).encode("utf-8")
    return MAGIC + struct.pack(">I", len(header)) + header + payload


def decompress(blob: bytes) -> bytes:
    if blob[:4] != MAGIC:
        raise ValueError("Not a Huffman-compressed file (bad signature).")

    (header_len,) = struct.unpack(">I", blob[4:8])
    header = json.loads(blob[8:8 + header_len].decode("utf-8"))
    payload = blob[8 + header_len:]

    freq = {int(k): v for k, v in header["freq"].items()}
    root = build_tree(freq)
    return decode(bytes_to_bits(payload), root, header["length"])


# --------------------------------------------------------------------------
# File helpers + statistics
# --------------------------------------------------------------------------
def compress_file(src: str, dst: str) -> dict:
    with open(src, "rb") as f:
        data = f.read()
    blob = compress(data)
    with open(dst, "wb") as f:
        f.write(blob)
    return compression_stats(len(data), len(blob))


def decompress_file(src: str, dst: str) -> int:
    with open(src, "rb") as f:
        blob = f.read()
    data = decompress(blob)
    with open(dst, "wb") as f:
        f.write(data)
    return len(data)


def compression_stats(original: int, compressed: int) -> dict:
    ratio = compressed / original if original else 0.0
    return {
        "original_bytes": original,
        "compressed_bytes": compressed,
        "ratio": ratio,
        "saved_percent": (1 - ratio) * 100 if original else 0.0,
    }
