import unittest

class TestImports(unittest.TestCase):
    def test_scanner_imports(self):
        import scanner.run  # noqa

if __name__ == "__main__":
    unittest.main()
