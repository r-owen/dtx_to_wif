__all__ = ["read_pattern_data", "read_pattern_file", "SupportedFileSuffixes"]

import base64
import dataclasses
import io
import pathlib
from collections.abc import Callable
from os import PathLike
from typing import Any

from .dtx_reader import read_dtx
from .pattern_data import PatternData
from .wif_reader import read_wif
from .wpo_reader import read_wpo


@dataclasses.dataclass
class ReaderInfo:
    reader: Callable[[Any, str], PatternData]
    is_binary: bool


#: A dict of file suffix: ReaderInfo
Readers = {
    ".dtx": ReaderInfo(reader=read_dtx, is_binary=False),
    ".wif": ReaderInfo(reader=read_wif, is_binary=False),
    ".wpo": ReaderInfo(reader=read_wpo, is_binary=True),
}

#: File suffixes supported by `read_pattern_data`
SupportedFileSuffixes = set(Readers.keys())


def read_pattern_data(data: str, suffix: str, name: str):
    """Read a weaving pattern from a data string.

    For WeavePoint .wpo files, which are binary, encode the data as base64,
    e.g. using `base64.b64decode(data_bytes)`.

    Args:
        data:  Pattern data. WeavePoint data must be encoded as base64.
        suffix: Pattern file suffix: one of ".dtx", ".wif", ".wpo".
        name: Pattern name. Typically the file name (including suffix).
    """
    suffix_lower = suffix.lower()
    reader_info = Readers.get(suffix_lower)
    if reader_info is None:
        raise NotImplementedError(
            f"Cannot read {suffix_lower} data: must be one of {Readers.keys()}"
        )
    if reader_info.is_binary:
        with io.BytesIO(base64.b64decode(data)) as f:
            return reader_info.reader(f, name)
    else:
        with io.StringIO(data) as f:
            return reader_info.reader(f, name)


def read_pattern_file(filepath: PathLike | str) -> PatternData:
    """Read a weaving pattern file

    Args:
        filepath: Path to file.
    """
    filepath = pathlib.Path(filepath)
    suffix_lower = filepath.suffix.lower()
    reader_info = Readers.get(suffix_lower)
    if reader_info is None:
        raise NotImplementedError(
            f"Cannot read {suffix_lower} files: must be one of {Readers.keys()}"
        )

    with filepath.open("rb" if reader_info.is_binary else "r") as f:
        return reader_info.reader(f, filepath.name)
