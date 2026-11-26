"""Run with:  python -m unittest -v"""

import os
import tempfile
import unittest

import huffman as hf


class TestHuffman(unittest.TestCase):
    def roundtrip(self, data: bytes):
        self.assertEqual(hf.decompress(hf.compress(data)), data)

    def test_normal_text(self):
        self.roundtrip(b"this is an example of a huffman tree")

    def test_empty_file(self):
        self.roundtrip(b"")

    def test_single_character(self):
        self.roundtrip(b"a")

    def test_one_repeated_character(self):
        self.roundtrip(b"aaaaaaaaaa")

    def test_two_symbols(self):
        self.roundtrip(b"abababbbbaaa")

    def test_all_256_byte_values(self):
        self.roundtrip(bytes(range(256)) * 3)

    def test_unicode_text(self):
        self.roundtrip("नमस्ते दुनिया - héllo wörld ✓".encode("utf-8"))

    def test_codes_are_prefix_free(self):
        data = b"abracadabra alakazam"
        codes = list(hf.generate_codes(hf.build_tree(hf.build_frequency_table(data))).values())
        for i, a in enumerate(codes):
            for j, b in enumerate(codes):
                if i != j:
                    self.assertFalse(b.startswith(a), f"{a} is a prefix of {b}")

    def test_frequent_symbols_get_shorter_codes(self):
        data = b"aaaaaaaaaabbbbbcc d"
        freq = hf.build_frequency_table(data)
        codes = hf.generate_codes(hf.build_tree(freq))
        self.assertLessEqual(len(codes[ord("a")]), len(codes[ord("d")]))

    def test_known_optimal_length(self):
        # Classic example: total encoded bits for this text is 135.
        data = b"this is an example of a huffman tree"
        codes = hf.generate_codes(hf.build_tree(hf.build_frequency_table(data)))
        self.assertEqual(sum(len(codes[b]) for b in data), 135)

    def test_repetitive_text_shrinks(self):
        data = b"the quick brown fox jumps over the lazy dog. " * 500
        self.assertLess(len(hf.compress(data)), len(data))

    def test_bad_signature_rejected(self):
        with self.assertRaises(ValueError):
            hf.decompress(b"NOPE" + b"\x00" * 20)

    def test_file_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            src, comp, out = (os.path.join(d, n) for n in ("a.txt", "a.huff", "a.out"))
            with open(src, "wb") as f:
                f.write(b"hello huffman " * 100)
            hf.compress_file(src, comp)
            hf.decompress_file(comp, out)
            with open(src, "rb") as a, open(out, "rb") as b:
                self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
