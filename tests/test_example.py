import unittest


class TestExample(unittest.TestCase):
    def test_simple_assertion(self):
        self.assertEqual(1 + 1, 2, "Simple addition should work")


if __name__ == "__main__":
    unittest.main()
