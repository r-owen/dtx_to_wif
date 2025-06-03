# Version History

## 4.3.1 2025-06-03

Fix an incompatibility with Python older than 3.12.
Document 3.10 as the earliest supported version of Python. (3.9 does not work.)

## 4.3 2025-05-01

Add API documentation using MkAPI.

Change code documentation from numpy to google doc format.

## 4.2.1 2025-04-28

Add mkdocs documentation, including a version history.

Update github links to point to dtx_to_wif instead of dtx_to_wif_converter.

## 4.2 2025-04-18

Add `read_pattern_data` and `read_pattern_file` functions, which read any supported file format.
This is now the recommended way to read pattern files.

Fix reading WeavePoint files with multi-byte masks.

Improve WeavePoint test data.

At this point I consider WeavePoint .wpo files support to be release quality.
The code still cannot read thread thickness and separation, but adding that would require information from the WeavePoint folks that they have been reluctant to provide, or risky reverse-engineering.

## 4.1.1 2025-04-07

Fix color range when reading WeavePoint files

## 4.1 2025-04-03

Factor out common code between `run_dtx_to_wif` and `run_wpo_to_wif` into a new internal function.

## 4.0 2025-04-02

Add experimental support for reading WeavePoint .wpo files and converting them to WIF files.

## 3.2 2025-03-13

Update the ReadMe.

Move test data into the package and use standard packaging tools to read them.

Remove pytest as a requirement.

## 3.1.0 2025-03-13

Bug fix: read_wif failed on files with no value after the key

## 3.0.2 2025-01-27

ReadMe.md: clarify an instruction.

PatternData: fix a doc string.

Simplify the way the build system (pyproject.toml) finds non-Python files.

## 3.0.1 2024-12-07

Add py.typed file so that other software can see this package's type hints (e.g. when running mypy).

## 3.0 2024-11-25

Rename the `DrawdownData` class to `PatternData`, and generally use the term "pattern" or "weaving pattern" instead of "drawdown.
This should only affect software that uses `dtx_to_wif` as a library.

## 2.0 2024-09-23

* Make a pip-installable package.
* Add `read_wif` function to read WIF files.
* Rename the dtx reader to `read_dtx`.
* Rename the WIF writer to `write_wif`.
* Read file data into `DrawdownData`, a dataclass that is intended to model the WIF standard.
* Expand the unit tests.

## 1.2 2024-06-10

Unify color and separation handling:

* If all values are default, omit the relevant section.
* If any values are not default, list the value for every end or pick.

Add a unit test.

## 1.1 2024-06-10

Bug fix: only folders (not files) could be specified as input.

## 1.0 2024-06-08

First release
