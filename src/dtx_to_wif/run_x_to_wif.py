__all__ = ["run_dtx_to_wif", "run_wpo_to_wif"]

import argparse
import pathlib
import traceback

from .pattern_reader import SupportedFileSuffixes, read_pattern_file
from .wif_writer import write_wif


def run_x_to_wif(suffix: str) -> None:
    """Command-line script to convert weaving pattern files to WIF format.

    Note: the readers all accept opened files, instead of file paths,
    in order to support data from a bytes or stream.

    Args:
        suffix: File suffix, including a leading period.
            Must be one of the entries in `SupportedFileSuffixes`.
    """
    if suffix not in SupportedFileSuffixes:
        supported_prefixes_str = ", ".join(sorted(SupportedFileSuffixes))
        raise NotImplementedError(
            f"Cannot read {suffix} files: must be one of {supported_prefixes_str}"
        )
    parser = argparse.ArgumentParser(description=f"Convert {suffix} files to WIF files")
    parser.add_argument(
        "inpath", nargs="+", help=f"{suffix} files or directories of files to parse"
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="overwrite existing files?"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="print parsed data"
    )
    args = parser.parse_args()

    # We want to accept individual files as well as directory paths,
    # but path.rglob("*{suffix}") returns nothing if path is a file.
    # Work around this by accumulating all file paths in advance.
    # Also purge duplicates while preserving order by using a dict
    # (we only need a set of paths, but set does not preserve order).
    infiles: dict[pathlib.Path, None] = dict()
    for infilestr in args.inpath:
        inpath = pathlib.Path(infilestr)
        if inpath.suffix == suffix:
            infiles[inpath] = None
        else:
            infiles.update((infile, None) for infile in inpath.rglob(f"*{suffix}"))

    for infile in infiles:
        outfile = infile.with_suffix(".wif")
        if outfile.exists():
            if args.overwrite:
                print(f"Overwriting existing {outfile}")
            else:
                print(f"Skipping existing {outfile}")
                continue
        else:
            print(f"Writing {outfile}")

        try:
            pattern = read_pattern_file(infile)
        except Exception:
            traceback.print_exc()
            print(f"Failed to read {infile}")
            continue
        try:
            with outfile.open("w") as outf:
                write_wif(outf, pattern)
        except Exception:
            traceback.print_exc()
            print(f"Failed to write {outfile}")
            continue

        if args.verbose:
            print(pattern)


def run_dtx_to_wif() -> None:
    """Command-line script to convert FiberWorks .dtx files to WIF."""
    run_x_to_wif(".dtx")


def run_wpo_to_wif() -> None:
    """Command-line script convert WeavePoint .wpo files to WIF."""
    run_x_to_wif(".wpo")
