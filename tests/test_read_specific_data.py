import importlib.resources
import unittest

from dtx_to_wif import TreadlingType, WarpWeftData, read_dtx, read_wif

datadir = importlib.resources.files("dtx_to_wif") / "../test_data"
basic_dtx_dir = datadir / "basic_dtx"
bad_wif_dir = datadir / "bad_dtx"

SpecificData = {
    "many color liftplan and zeros": {
        "name": "many color liftplan and zeros.dtx",
        "threading": {1: {2}, 2: {3}, 3: {4}, 4: {2}, 5: {1}},
        "tieup": {},
        "treadling": {},
        "liftplan": {
            1: {1, 3, 4},
            2: {3},
            3: {1, 2, 4},
            4: {1, 2, 3},
            5: {3, 4},
            6: {1},
        },
        "color_table": {
            1: (255, 255, 255),
            2: (255, 0, 0),
            3: (0, 255, 0),
            4: (0, 0, 255),
            5: (170, 170, 170),
            6: (0, 0, 0),
            7: (255, 255, 15),
            8: (255, 20, 255),
            9: (30, 255, 255),
            10: (150, 50, 255),
        },
        "warp": WarpWeftData(
            threads=5,
            color=3,
            color_rgb=None,
            spacing=0.212,
            thickness=None,
            units="centimeters",
        ),
        "weft": WarpWeftData(
            threads=6,
            color=8,
            color_rgb=None,
            spacing=0.212,
            thickness=None,
            units="centimeters",
        ),
        "warp_colors": {2: 4, 3: 5, 4: 1, 5: 2},
        "warp_spacing": {2: 0.159, 3: 0.106, 4: 0.053},
        "warp_thickness": {},
        "weft_colors": {2: 9, 3: 10, 4: 6, 5: 7},
        "weft_spacing": {1: 0.053, 2: 0.106, 3: 0.159, 5: 0.265, 6: 0.318},
        "weft_thickness": {},
        "color_range": (0, 255),
        "is_rising_shed": True,
        "source_program": "Fiberworks PCW",
        "source_version": "4.2",
        "num_shafts": 4,
        "num_treadles": 4,
        "treadling_type": TreadlingType.Liftplan,
        "notes": {
            1: "Line 1 of notes",
            2: "Another line of notes",
            3: "The final line of notes",
        },
        "private_sections": {},
    },
    "many color multiple treadles and zeros": {
        "name": "many color multiple treadles and zeros.dtx",
        "threading": {1: {2}, 2: {3}, 3: {4}, 5: {1}},
        "tieup": {1: {1, 3}, 2: {2, 4}, 3: {1}, 4: {2}, 5: {3}, 6: {4}},
        "treadling": {1: {1, 6}, 2: {5}, 3: {2, 3, 4}, 4: {0, 1, 4}, 5: {5, 6}, 6: {3}},
        "liftplan": {},
        "color_table": {
            1: (255, 255, 255),
            2: (255, 0, 0),
            3: (0, 255, 0),
            4: (0, 0, 255),
            5: (170, 170, 170),
            6: (0, 0, 0),
            7: (255, 255, 15),
            8: (255, 20, 255),
            9: (30, 255, 255),
            10: (150, 50, 255),
        },
        "warp": WarpWeftData(
            threads=5,
            color=3,
            color_rgb=None,
            spacing=0.212,
            thickness=None,
            units="centimeters",
        ),
        "weft": WarpWeftData(
            threads=6,
            color=8,
            color_rgb=None,
            spacing=0.212,
            thickness=None,
            units="centimeters",
        ),
        "warp_colors": {2: 4, 3: 5, 4: 1, 5: 2},
        "warp_spacing": {2: 0.159, 3: 0.106, 4: 0.053},
        "warp_thickness": {},
        "weft_colors": {2: 9, 3: 10, 4: 6, 5: 7},
        "weft_spacing": {1: 0.053, 2: 0.106, 3: 0.159, 5: 0.265, 6: 0.318},
        "weft_thickness": {},
        "color_range": (0, 255),
        "is_rising_shed": True,
        "source_program": "Fiberworks PCW",
        "source_version": "4.2",
        "num_shafts": 4,
        "num_treadles": 6,
        "treadling_type": TreadlingType.MultiTreadle,
        "notes": {},
        "private_sections": {},
    },
}


class TestReadSpecificData(unittest.TestCase):
    def test_read_specific_data_from_wif(self):
        for filename, expected_data in SpecificData.items():
            with self.subTest(filename=filename):
                wif_path = datadir / "desired_basic_wif" / (filename + ".wif")
                with wif_path.open("r") as f:
                    parsed_wif = read_wif(f)
                assert vars(parsed_wif) == expected_data

    def test_read_specific_data_from_dtx(self):
        for filename, expected_data in SpecificData.items():
            with self.subTest(filename=filename):
                dtx_path = datadir / "basic_dtx" / (filename + ".dtx")
                with dtx_path.open("r") as f:
                    parsed_dtx = read_dtx(f)
                assert vars(parsed_dtx) == expected_data


if __name__ == "__main__":
    unittest.main()
