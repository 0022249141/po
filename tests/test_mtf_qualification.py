import tempfile
import unittest
from pathlib import Path

from research_core.mtf_qualification import qualify_bundle


BAR_HEADER = "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\n"
TICK_HEADER = "<DATE>\t<TIME>\t<BID>\t<ASK>\t<LAST>\t<VOLUME>\t<FLAGS>\n"


class MultiTimeframeQualificationTests(unittest.TestCase):
    def test_exact_reconstruction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            m5 = root / "m5.csv"
            m15 = root / "m15.csv"
            h1 = root / "h1.csv"
            tick = root / "tick.csv"

            m5_rows = []
            tick_rows = []
            values = []
            for i in range(12):
                minute = i * 5
                hour = minute // 60
                mm = minute % 60
                value = 100.0 + i
                values.append(value)
                m5_rows.append(f"2026.01.01\t{hour:02d}:{mm:02d}:00\t{value:.2f}\t{value:.2f}\t{value:.2f}\t{value:.2f}\t1\t0\t10\n")
                tick_rows.append(f"2026.01.01\t{hour:02d}:{mm:02d}:00.000\t{value:.2f}\t{value + 0.10:.2f}\t\t\t6\n")

            m15_rows = []
            for block in range(4):
                subset = values[block * 3:(block + 1) * 3]
                minute = block * 15
                m15_rows.append(
                    f"2026.01.01\t00:{minute:02d}:00\t{subset[0]:.2f}\t{max(subset):.2f}\t{min(subset):.2f}\t{subset[-1]:.2f}\t3\t0\t10\n"
                )

            h1_rows = ["2026.01.01\t00:00:00\t100.00\t111.00\t100.00\t111.00\t12\t0\t10\n"]
            # Extra boundary tick establishes a cutoff at 01:00 without altering the 00:00 H1 bucket.
            tick_rows.append("2026.01.01\t01:00:00.000\t112.00\t112.10\t\t\t6\n")

            m5.write_text(BAR_HEADER + "".join(m5_rows), encoding="utf-8")
            m15.write_text(BAR_HEADER + "".join(m15_rows), encoding="utf-8")
            h1.write_text(BAR_HEADER + "".join(h1_rows), encoding="utf-8")
            tick.write_text(TICK_HEADER + "".join(tick_rows), encoding="utf-8")

            result = qualify_bundle(h1_path=h1, m15_path=m15, m5_path=m5, tick_path=tick)

            self.assertEqual(result["cross_timeframe"]["M5_to_M15"]["ohlc_mismatches"], 0)
            self.assertEqual(result["cross_timeframe"]["M5_to_H1"]["ohlc_mismatches"], 0)
            self.assertEqual(result["cross_timeframe"]["M15_to_H1"]["ohlc_mismatches"], 0)
            self.assertEqual(result["tick_reconstruction"]["M5"]["ohlc_mismatches"], 0)
            self.assertEqual(result["tick_reconstruction"]["M15"]["ohlc_mismatches"], 0)
            self.assertEqual(result["tick_reconstruction"]["H1"]["ohlc_mismatches"], 0)
            self.assertEqual(result["latest_closed_bar"]["H1"], "2026-01-01T00:00:00")


if __name__ == "__main__":
    unittest.main()
