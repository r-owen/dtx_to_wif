__all__ = ["read_twa"]

import io
import zipfile
from typing import BinaryIO

from .pattern_data import PatternData
from .wif_reader import read_wif

# The name of the WIF file contained in the TempoWeave twa zip archive.
WIF_FILE_NAME = "twamain.waf"


def read_twa(f: BinaryIO, filename: str = "?") -> PatternData:
    """Read a TempoWeave twa weaving file as PatternData.

    Args:
        f: A readable binary file
        filename: The file name. Usually ignored, but used as the pattern name
            if the wif file inside the twa file does not have
            a Title line in the [TEXT] section.
    """
    with zipfile.ZipFile(f, mode="r") as zf:
        with zf.open(WIF_FILE_NAME, mode="r") as wif_binary_file:
            wif_text_file = io.TextIOWrapper(wif_binary_file, encoding="utf-8")
            return read_wif(wif_text_file, filename=filename)
