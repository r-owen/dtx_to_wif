import importlib.resources
import unittest
from typing import Any

from dtx_to_wif import TreadlingType, read_dtx, read_wif

datadir = importlib.resources.files("dtx_to_wif") / "../test_data"
basic_dtx_dir = datadir / "basic_dtx"
bad_wif_dir = datadir / "bad_dtx"


class TestWifReader(unittest.TestCase):
    def test_wif_reader_compared_to_dtx_reader(self):
        for dtx_path in basic_dtx_dir.glob("*.dtx"):
            with self.subTest(file=dtx_path.stem):
                wif_path = datadir / "desired_basic_wif" / (dtx_path.stem + ".wif")
                with open(dtx_path, "r") as f:
                    parsed_dtx = read_dtx(f)
                with open(wif_path, "r") as f:
                    parsed_wif = read_wif(f)
                assert parsed_dtx == parsed_wif

    def test_read_bad_files(self):
        for wif_path_path in bad_wif_dir.rglob("*.wif"):
            with self.subTest(file=wif_path_path.name):
                with open(wif_path_path, "r") as f:
                    with self.assertRaises(RuntimeError):
                        read_wif(f)

    def assert_dicts_of_float_almost_equal(
        self, dict1: dict[Any, float], dict2: dict[Any, float]
    ) -> None:
        assert set(dict1.keys()) == set(dict2.keys())
        for key in dict1:
            self.assertAlmostEqual(dict1[key], dict2[key])

    def test_default_values(self):
        wif_path = datadir / "basic_wif" / "treadles with defaults.wif"
        with open(wif_path, "r") as f:
            parsed_wif = read_wif(f)
        assert parsed_wif.liftplan == {}
        assert parsed_wif.tieup == {1: {1}, 2: {2, 4}}
        assert parsed_wif.treadling == {1: {1, 6}, 2: {5}, 3: {0, 2, 5}}
        assert parsed_wif.treadling_type == TreadlingType.MultiTreadle
        assert parsed_wif.warp_colors == {2: 4, 5: 2}
        assert parsed_wif.weft_colors == {3: 10, 5: 7}
        self.assert_dicts_of_float_almost_equal(
            parsed_wif.warp_spacing, {2: 0.159, 4: 0.053}
        )
        self.assert_dicts_of_float_almost_equal(
            parsed_wif.weft_spacing, {1: 0.053, 2: 0.106}
        )

    def test_default_liftplan_values(self):
        wif_path = datadir / "basic_wif" / "liftplan with defaults.wif"
        with open(wif_path, "r") as f:
            parsed_wif = read_wif(f)
        assert parsed_wif.liftplan == {1: {1, 2, 4}, 4: {0, 3, 4}}


if __name__ == "__main__":
    unittest.main()
