from scanner.fib import fib_levels


def test_fib_levels_monotonic():
    levels = fib_levels(0.0, 100.0)
    vals = [levels[k] for k in ["0.382","0.5","0.618","0.786"]]
    assert vals[0] > vals[1] > vals[2] > vals[3]
