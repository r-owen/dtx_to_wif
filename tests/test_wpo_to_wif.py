import importlib.resources
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from dtx_to_wif import read_wif

datadir = importlib.resources.files("dtx_to_wif") / "../test_data"

ACTUAL_DIR = "basic_wpo"
EXPECTED_DIR = "desired_basic_wif"


class TestWpoToWif(unittest.TestCase):
    """Test wpo_to_wif command-line script."""

    def test_wpo_to_wif(self):
        cmdname = "wpo_to_wif"
        # Copy test_data to a temp dir and run wpo_to_wif on the copied files,
        # to avoid writing files to test_data
        with tempfile.TemporaryDirectory() as tempdirname:
            tempdir = pathlib.Path(tempdirname)
            for subdirname in (ACTUAL_DIR, EXPECTED_DIR):
                shutil.copytree(datadir / subdirname, tempdir / subdirname)

            actual_dir = tempdir / ACTUAL_DIR
            actual_dir_str = actual_dir.as_posix()
            expected_dir = tempdir / EXPECTED_DIR
            result = subprocess.run(
                [cmdname, actual_dir_str], check=True, capture_output=True
            )
            self.check_run_result(result, desired_prefix="Writing")
            actual_paths = [path for path in actual_dir.rglob("*.wpo")]
            assert len(actual_paths) == 9
            for wpo_path in actual_paths:
                wif_path = wpo_path.with_suffix(".wif")
                assert wif_path.is_file()
                expected_wif_path = expected_dir / wif_path.name
                self.assert_files_equal(wif_path, expected_wif_path)

            # Clear the wif files in the basic_wpo dir tree and run again.
            # All wif files should be empty because they are not overwritten.
            for wpo_path in actual_paths:
                wif_path = wpo_path.with_suffix(".wif")
                with wif_path.open("w") as f:
                    f.truncate()
            result = subprocess.run(
                [cmdname, actual_dir_str], check=True, capture_output=True
            )
            self.check_run_result(result, desired_prefix="Skipping")
            for wpo_path in actual_paths:
                wif_path = wpo_path.with_suffix(".wif")
                assert wif_path.is_file()
                with wif_path.open("r") as f:
                    data = f.read()
                    assert data == ""

            # Check that --overwrite replaces the (currently empty) wif files
            # and check that individual files can be specified
            # (instead of, or in addition to, directories)
            filepathargs = [cmdname] + actual_paths + ["--overwrite"]
            result = subprocess.run(filepathargs, check=True, capture_output=True)
            self.check_run_result(result, desired_prefix="Overwriting")
            for wpo_path in actual_paths:
                wif_path = wpo_path.with_suffix(".wif")
                assert wif_path.is_file()
                expected_wif_path = datadir / EXPECTED_DIR / wif_path.name
                self.assert_files_equal(wif_path, expected_wif_path)

    def check_run_result(self, result, desired_prefix):
        """Check the result from running the function.

        Args:
            result: Return value from subprocess.run_result,
                which must be configured to capture stderr and stdout.
            desired_prefix: The desired beginning of each line of stdout.
        """
        with self.subTest(result=result, desired_prefix=desired_prefix):
            assert result.returncode == 0
            assert result.stderr == b""
            for line in result.stdout.decode().split("\n"):
                if line:
                    assert line.startswith(desired_prefix)

    def assert_files_equal(self, actual_path, expected_path):
        """Compare the actual wif file to the desired wif file."

        Allow the actual wif file to have extra ends and picks
        and check that they have the expected associated values.
        """
        with self.subTest(actual_path=actual_path, expected_path=expected_path):
            with actual_path.open("r") as file1:
                actual_data = read_wif(file1)
            with expected_path.open("r") as file2:
                expected_data = read_wif(file2)

            assert actual_data.name == actual_path.with_suffix(".wpo").name
            assert actual_data.source_program == "WeavePoint"
            assert actual_data.source_version == "7"

            for fieldname in (
                "threading",
                "tieup",
                "liftplan",
                "color_range",
                "is_rising_shed",
                "num_shafts",
                "num_treadles",
            ):
                with self.subTest(fieldname=fieldname):
                    assert getattr(actual_data, fieldname) == getattr(
                        expected_data, fieldname
                    )

            # WeavePoint does not preserve treadle 0
            assert expected_data.treadling.keys() == actual_data.treadling.keys()
            for key in expected_data.treadling:
                assert actual_data.treadling[key] - {0} == expected_data.treadling[
                    key
                ] - {0}

            # Compare color tables, ignoring keys not in the actual data
            for key, value in expected_data.color_table.items():
                assert actual_data.color_table[key] == value

            # Compare warp and weft colors.
            for direction in ("warp", "weft"):
                actual_colors = getattr(actual_data, f"{direction}_colors")
                expected_colors = getattr(expected_data, f"{direction}_colors")
                actual_default = getattr(actual_data, direction).color
                expected_default = getattr(expected_data, direction).color
                num_threads = getattr(expected_data, direction).threads
                expected_threads_set = set(range(1, num_threads + 1))
                # Check that there are no actual or expected thread colors
                # for threads that are out of the expected range
                assert actual_colors.keys() - expected_threads_set == set()
                assert expected_colors.keys() - expected_threads_set == set()

                # Compare colors for all threads that were in the original
                # wif file that was read into WeavePoint to produce
                # the .wpo file. Any additional threads that WeavePoint
                # added (and there will be many) need not match.
                for thread in expected_threads_set:
                    assert expected_colors.get(
                        thread, expected_default
                    ) == actual_colors.get(thread, actual_default)

            # The code cannot read thread spacing or thickness
            for fieldname in (
                "warp_spacing",
                "warp_thickness",
                "weft_spacing",
                "weft_thickness",
            ):
                with self.subTest(fieldname=fieldname):
                    assert getattr(actual_data, fieldname) == {}

    def compare_dicts(self, actual, expected, actual_default, expected_default):
        for key, value in expected.items():
            assert actual.get(key, actual_default) == value
        for extra_key in actual.keys() - expected.keys():
            assert actual[extra_key] == actual_default


if __name__ == "__main__":
    unittest.main()
