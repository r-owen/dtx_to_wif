import importlib.resources
import unittest

from dtx_to_wif import read_dtx, read_wif

datadir = importlib.resources.files("dtx_to_wif") / "../test_data"
bad_dtx_dir = datadir / "bad_dtx"
basic_dtx_dir = datadir / "basic_dtx"


class TestDtxReader(unittest.TestCase):
    def test_read_bad_files(self):
        # Note: a few errors are not possible in dtx files,
        # since the data is in lists, not dicts. Test what we can.
        for dtx_file_path in bad_dtx_dir.rglob("*.dtx"):  # type: ignore
            with self.subTest(file=dtx_file_path.name):
                with dtx_file_path.open("r") as f:
                    with self.assertRaises(RuntimeError):
                        read_dtx(f)

    def test_read_dtx_compared_to_read_wif(self):
        files_found = 0
        for dtx_path in basic_dtx_dir.rglob("*.dtx"):  # type: ignore
            files_found += 1
            with self.subTest(file=dtx_path.stem):
                wif_path = datadir / "desired_basic_wif" / (dtx_path.stem + ".wif")
                with dtx_path.open("r") as f:
                    parsed_dtx = read_dtx(f)
                with wif_path.open("r") as f:
                    parsed_wif = read_wif(f)
                assert parsed_dtx == parsed_wif
        assert files_found == 5


if __name__ == "__main__":
    unittest.main()
