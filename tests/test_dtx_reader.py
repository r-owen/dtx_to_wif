import importlib.resources
import unittest

from dtx_to_wif import read_dtx

bad_dtx_dir = importlib.resources.files("dtx_to_wif") / "../test_data/bad_dtx"


class TestDtxReader(unittest.TestCase):
    def test_read_bad_files(self):
        # Note: a few errors are not possible in dtx files,
        # since the data is in lists, not dicts. Test what we can.
        for dtx_file_path in bad_dtx_dir.rglob("*.dtx"):
            with self.subTest(file=dtx_file_path.name):
                with dtx_file_path.open("r") as f:
                    with self.assertRaises(RuntimeError):
                        read_dtx(f)


if __name__ == "__main__":
    unittest.main()
