import unittest
import pandas as pd
import numpy as np

from scanner.indicators import add_indicators

class TestFairValue(unittest.TestCase):
    def test_fv_columns_exist_and_1d(self):
        n = 300
        idx = pd.date_range("2023-01-01", periods=n, freq="D")
        rng = np.random.default_rng(0)
        price = 100 + np.cumsum(rng.normal(0, 1, size=n))
        high = price + rng.uniform(0.5, 2.0, size=n)
        low = price - rng.uniform(0.5, 2.0, size=n)
        open_ = price + rng.normal(0, 0.5, size=n)
        close = price
        vol = rng.integers(1_000_000, 5_000_000, size=n)

        df = pd.DataFrame({
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": vol
        }, index=idx)

        d = add_indicators(df)
        self.assertIn("fv_vwap_20", d.columns)
        self.assertIn("fv_low", d.columns)
        self.assertIn("fv_high", d.columns)

        # Ensure they are Series-like (not DataFrame columns)
        self.assertTrue(pd.api.types.is_numeric_dtype(d["fv_vwap_20"]))
        self.assertEqual(len(d["fv_vwap_20"].shape), 1)

    def test_no_duplicate_columns(self):
        n = 50
        df = pd.DataFrame({"open": range(n), "high": range(n), "low": range(n), "close": range(n), "volume": range(n)})
        d = add_indicators(df)
        self.assertFalse(d.columns.duplicated().any())

if __name__ == "__main__":
    unittest.main()
