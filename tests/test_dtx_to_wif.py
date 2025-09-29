import importlib.resources
import pathlib
import shutil
import subprocess
import tempfile
import unittest

datadir = importlib.resources.files("dtx_to_wif") / "../test_data"
ACTUAL_SUBDIR = "basic_dtx"
EXPECTED_SUBDIR = "desired_basic_wif"


class TestDtxToWif(unittest.TestCase):
    def test_dtx_to_wif(self):
        cmdname = "dtx_to_wif"
        # Copy test_data to a temp dir and run dtx_to_wif on the copied files,
        # to avoid writing files to test_data
        with tempfile.TemporaryDirectory() as tempdirname:
            tempdir = pathlib.Path(tempdirname)
            for subdirname in (ACTUAL_SUBDIR, EXPECTED_SUBDIR):
                shutil.copytree(datadir / subdirname, tempdir / subdirname)

            actual_dir = tempdir / ACTUAL_SUBDIR
            actual_dir_str = actual_dir.as_posix()
            desired_basic_wif_dir = tempdir / EXPECTED_SUBDIR
            result = subprocess.run(
                [cmdname, actual_dir_str], check=True, capture_output=True
            )
            self.check_run_result(result, desired_prefix="Writing")
            actual_paths = [path for path in actual_dir.rglob("*.dtx")]
            assert len(actual_paths) == 6
            for dtxpath in actual_paths:
                wif_path = dtxpath.with_suffix(".wif")
                assert wif_path.is_file()
                actual_wif_path = desired_basic_wif_dir / wif_path.name
                self.assert_files_equal(wif_path, actual_wif_path)

            # Clear the wif files in the basic_dtx dir tree and run again.
            # All wif files should be empty because they are not overwritten.
            for dtxpath in actual_paths:
                wif_path = dtxpath.with_suffix(".wif")
                with wif_path.open("w") as f:
                    f.truncate()
            result = subprocess.run(
                [cmdname, actual_dir_str], check=True, capture_output=True
            )
            self.check_run_result(result, desired_prefix="Skipping")
            for dtxpath in actual_paths:
                wif_path = dtxpath.with_suffix(".wif")
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
            for dtxpath in actual_paths:
                wif_path = dtxpath.with_suffix(".wif")
                assert wif_path.is_file()
                actual_wif_path = datadir / EXPECTED_SUBDIR / wif_path.name
                self.assert_files_equal(wif_path, actual_wif_path)

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

    def assert_files_equal(self, path1, path2):
        with self.subTest(path1=path1, path2=path2):
            with path1.open("r") as file1:
                data1 = file1.read()
            with path2.open("r") as file2:
                data2 = file2.read()
            assert data1 == data2


if __name__ == "__main__":
    unittest.main()
