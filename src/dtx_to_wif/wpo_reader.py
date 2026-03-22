__all__ = ["read_wpo"]

import enum
import warnings
from typing import BinaryIO

from .binary_file_reader import BinaryFileReader
from .pattern_data import PatternData, WarpWeftData

# The required value of the first byte for this to be a WeavePoint file
WPO_ID = 123


class FileTypes(enum.IntEnum):
    """File types are:

    LIFTPLAN:
        Liftplan is present;
        tie-up, single treadling, and multiple treadling are not.
    SINGLE_TREADLING:
        Tie-up and single treadling are present;
        liftplan and multiple treadling are not.
    MULTIPLE_TREADLING:
        Tie-up and multiple treadling are present;
        liftplan and single treadling are not.
    """

    LIFTPLAN = 100
    SINGLE_TREADLING = 101
    MULTIPLE_TREADLING = 102


def read_wpo(f: BinaryIO, filename: str) -> PatternData:
    """Read a WeavePoint wpo weaving file as PatternData

    Does not read per-thread thickness and separation are not read,
    because the company has not told me how to access that information.

    Args:
        f: A readable binary file
        filename: The file name. Used as the pattern name.
    """
    bfr = BinaryFileReader(f=f, big_endian=True)
    id_code = bfr.read_uint8()
    if id_code != WPO_ID:
        raise RuntimeError(f"ID code {id_code} != {WPO_ID}")

    file_version = bfr.read_uint8()
    if file_version > 7:
        warnings.warn("File version > 7; the results may not be correct")
    file_type_int = bfr.read_uint8()  # file type: 100=dobby  101=tie-up  102=tie-up II
    # TODO: when we require Python 3.12 or later, simplify this to:
    #     if file_type_int not in FileTypes:
    #         ...raise RuntimeError...
    try:
        FileTypes(file_type_int)
    except ValueError:
        file_types_str = ", ".join(str(i) for i in FileTypes)
        raise RuntimeError(f"Unknown {file_type_int=}; must be in {file_types_str}")
    file_type = FileTypes(file_type_int)
    bfr.read_uint8()  # zoom: a value between 1 and 20
    num_shafts = bfr.read_uint8()
    num_treadles = bfr.read_uint8()
    bfr.read_bytes(1)  # ignore a
    is_rising_shed = bfr.read_uint8() == 0
    bfr.read_bytes(1)  # ignore b
    epi = bfr.read_uint8()  # originally "ignore c"
    ppi = bfr.read_uint8()  # originally "ignore d"
    bfr.read_bytes(2)  # ignore e-f
    num_ends = bfr.read_uint16()
    num_picks = bfr.read_uint16()
    bfr.read_bytes(7)  # ignore g-m

    threading = {key: set([value]) for key, value in read_dict_of_int(bfr).items()}
    warp_colors = {key: value + 1 for key, value in read_dict_of_int(bfr).items()}
    weft_colors = {key: value + 1 for key, value in read_dict_of_int(bfr).items()}
    default_warp_color = warp_colors.get(len(warp_colors))
    default_weft_color = weft_colors.get(len(weft_colors))

    treadling: dict[int, set[int]] = {}
    liftplan: dict[int, set[int]] = {}
    tieup: dict[int, set[int]] = {}
    if file_type == FileTypes.LIFTPLAN:
        liftplan = read_bitmask_sequence(bfr, bits_per_mask=num_shafts)
    elif file_type == FileTypes.MULTIPLE_TREADLING:
        tieup = read_bitmask_sequence(
            bfr, bits_per_mask=num_shafts, num_masks=num_treadles
        )
        treadling = read_bitmask_sequence(bfr, bits_per_mask=num_treadles)
    else:
        # single treadling
        tieup = read_bitmask_sequence(
            bfr, bits_per_mask=num_shafts, num_masks=num_treadles
        )
        treadling = {key: set([value]) for key, value in read_dict_of_int(bfr).items()}

    bfr.read_bytes(66)  # ignore "translation grids"

    color_table_len = bfr.read_uint8()
    color_range = (0, 255) if file_version >= 4 else (0, 63)
    color_table: dict[int, tuple[int, int, int]] = {
        i + 1: read_rgb(bfr) for i in range(color_table_len)
    }

    return PatternData(
        name=filename,
        threading=threading,
        tieup=tieup,
        treadling=treadling,
        liftplan=liftplan,
        color_table=color_table,
        warp=WarpWeftData(
            threads=num_ends, color=default_warp_color, spacing=1 / epi, units="inches"
        ),
        weft=WarpWeftData(
            threads=num_picks, color=default_weft_color, spacing=1 / ppi, units="inches"
        ),
        warp_colors=warp_colors,
        warp_spacing={},
        warp_thickness={},
        weft_colors=weft_colors,
        weft_spacing={},
        weft_thickness={},
        color_range=color_range,
        is_rising_shed=is_rising_shed,
        source_program="WeavePoint",
        source_version=str(file_version),
        num_shafts=num_shafts,
        num_treadles=num_treadles,
    )


def mask_to_int_set(mask: int) -> set[int]:
    """Convert a bit mask to a set of 1-valued ints"""
    bititer = reversed(bin(mask)[2:])
    return {i + 1 for i, char in enumerate(bititer) if char == "1"}


def num_bytes_for_bits(num_bits: int) -> int:
    """Return the number of bytes required to hold num_bits bits"""
    if num_bits < 1:
        raise ValueError(f"{num_bits=} must be positive")
    return (num_bits - 1) // 8 + 1


def read_bitmask_sequence(
    bfr: BinaryFileReader, bits_per_mask: int, num_masks: int | None = None
) -> dict[int, set[int]]:
    """Read a sequence of bitmasks, e.g. tieup, liftplan, or multiple treadles.

    The data format is:

    * number of masks, encoded as two big-endian bytes: MSB, LSB,
      unless num_masks is not None, in which case that data section should
      not have 2 bytes of length. Tieup data is one section that does not have
      2 length bytes, since the length is the number of treadles.
    * sequence of bitmasks, where each bitmask has just enough bytes to hold
      "bits_per_mask" bits. Bytes are in little-endian order (LSB, ..., MSB).
      Shaft/treadle 1 is bit 1, shaft/treadle 2 is bit 2, etc.

    The result is a dict of 1-based index: set of 1-based ints representing
    high bits in the bitmask.

    May return bits > bits_per_mask, since it does not check for that.
    """
    if bits_per_mask < 1:
        raise RuntimeError(f"{bits_per_mask} < 1")

    bytes_per_mask = num_bytes_for_bits(bits_per_mask)

    if num_masks is None:
        num_masks = bfr.read_uint16()
    masks = [
        bfr.read_int(num_bytes=bytes_per_mask, signed=False, big_endian=False)
        for _ in range(num_masks)
    ]
    return {i + 1: mask_to_int_set(mask) for i, mask in enumerate(masks)}


def read_bytes(f: BinaryIO, num_bytes: int) -> bytes:
    """Read exactly num_bytes bytes (possibly using multiple reads).

    Raises EOFError if EOF seen, and ValueError if num_bytes < 1.
    """
    if num_bytes < 1:
        raise ValueError(f"{num_bytes=} must be positive")
    data = b""
    while True:
        new_data = f.read(num_bytes - len(data))
        if len(new_data) == 0:
            raise EOFError("File too short")
        data += new_data
        if len(data) == num_bytes:
            return data
        elif len(data) > num_bytes:
            raise RuntimeError("Bug! read {len(data)} bytes > {num_bytes=}")


def read_dict_of_int(bfr: BinaryFileReader) -> dict[int, int]:
    """Read a sequence of one-byte integers as a dict of int

    The input format is:

    * length as 2 bytes: MSB, LSB
    * integer1, integer2, ... (length vaues)

    Return as a dict of {1-based index: integer value}
    """
    datalen = bfr.read_uint16()
    return {i + 1: bfr.read_uint8() for i in range(datalen)}


def read_rgb(bfr: BinaryFileReader) -> tuple[int, int, int]:
    """Read one set of RGB values encoded as 3 bytes."""
    rgb_values = tuple(bfr.read_uint8() for _ in range(3))
    assert len(rgb_values) == 3  # make linter happy
    return rgb_values
