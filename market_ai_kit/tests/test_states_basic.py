import pandas as pd

from scanner.scorer import relative_strength


def test_relative_strength_sign():
    df = pd.DataFrame({"close": [100, 110]})
    bm = pd.DataFrame({"close": [100, 105]})
    assert relative_strength(df, bm, lookback_days=2) > 0
