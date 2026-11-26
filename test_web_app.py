"""Tests for the browser app's compression and restore responses."""

import unittest

import huffman as hf
import web_app


class TestWebApp(unittest.TestCase):
    def test_compression_response_contains_codes_and_verifies_roundtrip(self):
        data = bytes(range(256)) + b" Huffman" * 4
        result = web_app.compress_for_web(data)

        self.assertTrue(result["verified"])
        self.assertEqual(hf.decompress(web_app._read_bytes(result["compressed"])), data)
        self.assertEqual(len(result["codes"]), len(set(data)))
        self.assertEqual({row["byte"] for row in result["codes"]}, set(data))

    def test_decompression_response_restores_original_bytes(self):
        data = "Huffman ✓".encode("utf-8")
        result = web_app.decompress_for_web(hf.compress(data))

        self.assertEqual(web_app._read_bytes(result["data"]), data)
        self.assertEqual(result["bytes"], len(data))

    def test_rejects_malformed_base64(self):
        with self.assertRaisesRegex(ValueError, "valid base64"):
            web_app._read_bytes("not base64!")


if __name__ == "__main__":
    unittest.main()
