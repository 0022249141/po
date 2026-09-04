import unittest

from research_core.lookahead import scan_text


class LookaheadTests(unittest.TestCase):
    def test_centered_rolling(self):
        sample = "x = df.price.rolling(5, center=True).mean()"
        findings = scan_text(sample)
        self.assertTrue(any(f["code"] == "centered_rolling" for f in findings))

    def test_negative_shift(self):
        sample = "label = df.close.shift(-1)"
        findings = scan_text(sample)
        self.assertTrue(any(f["code"] == "negative_shift" for f in findings))

    def test_safe_shift(self):
        sample = "feature = df.close.shift(1)"
        findings = scan_text(sample)
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
