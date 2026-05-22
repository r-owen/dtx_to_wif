import importlib.resources
import unittest

from dtx_to_wif import read_twa, read_wif

datadir = importlib.resources.files("dtx_to_wif") / "../test_data"
basic_twa_dir = datadir / "basic_twa"


class TestTWAReader(unittest.TestCase):
    def test_read_twa_compared_to_read_wif(self):
        files_found = 0
        for twa_path in basic_twa_dir.rglob("*.twa"):
            files_found += 1
            if True:
                # with self.subTest(file=twa_path.stem):
                wif_path = twa_path.with_suffix(".wif")
                with twa_path.open("rb") as f:
                    parsed_twa = read_twa(f)
                with wif_path.open("r") as f:
                    parsed_wif = read_wif(f)
                assert parsed_twa == parsed_wif
        assert files_found == 7


if __name__ == "__main__":
    unittest.main()
