__all__ = ["diff_patterns", "run_diff_weaving"]

import argparse
import collections
import pathlib
from collections.abc import Sequence

from dtx_to_wif import PatternData, make_liftplan, read_pattern_file
from dtx_to_wif.pattern_data import WarpWeftNames


def diff_patterns(
    pattern1: PatternData,
    pattern2: PatternData,
) -> list[str]:
    """Compare two patterns and describe differences in drawdown or color.

    Args:
        pattern1: First pattern to compare
        pattern2: Second pattern to compare

    Returns:
        A list of strings describing differences.
        The list is empty if the files are the same.

    Raises:
        RuntimeError if color_range is None in pattern1 or pattern2.

    Notes:
        For threading, ignores shaft 0.

        For picks, compares actual shafts lifted (igoring shaft 0),
        so any combination of liftplan, single treadling,
        and multiple treadling, may compare equal.

        Ignores notes and private sections.

        Ignores yarn thickness and separation, because those are difficult
        to compare. Different programs quantize them differently,
        and some units cannot be converted to others, so it is unclear
        how to do this reliably well. Worse, if unit conversion is required,
        it is possible to get different results depending on the order
        in which the patterns are specified.
    """
    diff_strs: list[str] = []

    diff_strs += compare_shaft_dicts(
        name="threading", dict1=pattern1.threading, dict2=pattern2.threading
    )
    diff_strs += compare_picks(pattern1=pattern1, pattern2=pattern2)

    if pattern1.color_range is None or pattern2.color_range is None:
        print(
            "Warning: cannot compare thread colors because color_range is missing from one or both patterns"
        )
    else:
        for warp_weft in WarpWeftNames:
            diff_strs += compare_color_dicts(
                warp_weft=warp_weft, pattern1=pattern1, pattern2=pattern2
            )

    return diff_strs


def compare_color_dicts(
    warp_weft: WarpWeftNames, pattern1: PatternData, pattern2: PatternData
) -> list[str]:
    """Compare warp or weft colors for two patterns.

    Args:
        warp_weft: warp or weft?
        pattern1: First pattern to compare
        pattern2: Second pattern to compare

    Returns:
        A list of strings describing differences.

    Raises:
        RuntimeError if color_range is None in pattern1 or pattern2.
    """
    diff_strs: list[str] = []
    if pattern1.color_range is None or pattern2.color_range is None:
        raise RuntimeError(
            "Cannot compare colors; color range is missing from one or both patterns"
        )
    item_name = {"warp": "end", "weft": "pick"}[warp_weft]
    color_diff = collections.defaultdict(list)

    max_key = get_num_ends_or_picks(
        warp_weft=warp_weft, pattern1=pattern1, pattern2=pattern2
    )
    color_table1 = pattern1.color_table
    color_table2 = pattern2.color_table
    default_color1 = getattr(pattern1, warp_weft).color
    default_color2 = getattr(pattern2, warp_weft).color
    dict1 = getattr(pattern1, f"{warp_weft}_colors")
    dict2 = getattr(pattern2, f"{warp_weft}_colors")
    for key in range(1, max_key + 1):
        color_key1 = dict1.get(key, default_color1)
        color_key2 = dict2.get(key, default_color2)
        color1 = normalize_color(
            color_table1.get(color_key1, "error: not in color table"),
            pattern1.color_range,
        )
        color2 = normalize_color(
            color_table2.get(color_key2, "error: not in color table"),
            pattern2.color_range,
        )
        if color1 != color2:
            color_diff[(color1, color2)].append(key)
    if color_diff:
        for colors, keylist in color_diff.items():
            diff_strs.append(
                f"{warp_weft} color {colors[0]} != {colors[1]} for {item_name}s: {keylist}"
            )
    return diff_strs


def compare_picks(
    pattern1: PatternData,
    pattern2: PatternData,
) -> list[str]:
    """Compare two sets of picks.

    Args:
        pattern1: First pattern to compare
        pattern2: Second pattern to compare

    Returns:
        A list of strings describing differences.
    """
    liftplan1 = make_liftplan(pattern1)
    liftplan2 = make_liftplan(pattern2)
    return compare_shaft_dicts(name="picks", dict1=liftplan1, dict2=liftplan2)


def compare_shaft_dicts(
    name: str, dict1: dict[int, set[int]], dict2=[int, set[int]]
) -> list[str]:
    """Compare two dicts of key: shaft_set.

    Args:
        name: Kind of shaft set; one of "threading", "tieup",
            "treadling", "liftplan", or "picks"
        pattern1: First pattern to compare
        pattern2: Second pattern to compare

    Returns:
        A list of strings describing differences.

    Raises:
        KeyError: If name is not supported.
    """
    empty_set: set[int] = set()
    diff_strs: list[str] = []
    if dict1 == dict2:
        return []
    item_name = {
        "threading": "end",
        "tieup": "treadle",
        "treadling": "pick",
        "liftplan": "pick",
        "picks": "pick",
    }[name]
    if len(dict1) != len(dict2):
        diff_strs.append(f"{name} length differs: {len(dict1)} != {len(dict2)}")
    max_key = max(*dict1.keys(), *dict2.keys())
    for key in range(1, max_key + 1):
        diff = compare_shaft_sets(
            f"{name} {item_name}",
            key,
            dict1.get(key, empty_set),
            dict2.get(key, empty_set),
        )
        if diff is not None:
            diff_strs.append(diff)
    return diff_strs


def compare_shaft_sets(
    name: str, id: int, shafts1: set[int], shafts2: set[int]
) -> None | str:
    """Compare two shaft sets.

    Args:
        name: Kind of shaft set; one of "threading", "tieup",
            "treadling", or "liftplan"
        shafts1: First set of shafts to compare
        shafts2: Second set of shafts to compare

    Returns:
        None of the shaft sets match, else a string describing the difference.
    """
    shafts1 = shafts1 - {0}
    shafts2 = shafts2 - {0}
    if shafts1 != shafts2:
        return f"{name} {id} differs: {shafts1} != {shafts2}"
    return None


def get_num_ends_or_picks(
    warp_weft: WarpWeftNames, pattern1: PatternData, pattern2: PatternData
) -> int:
    """Get the number of warp ends or picks, depending on warp_weft.

    Args:
        warp_weft: warp or weft?
        meas_name: name of measurement
        pattern1: First pattern
        pattern2: Second pattern
    """
    match warp_weft:
        case "warp":
            return max(*pattern1.threading.keys(), *pattern2.threading.keys())
        case "weft":
            # max_key = max pick number from treadling or liftplan
            return max(
                *pattern1.treadling.keys(),
                *pattern2.treadling.keys(),
                *pattern1.liftplan.keys(),
                *pattern2.liftplan.keys(),
            )
    raise RuntimeError(f"Unsupported {warp_weft=}")


def normalize_color(
    color: Sequence[int] | str, color_range: Sequence[int]
) -> Sequence[int] | str:
    """Normalize an RGB color sequence, returning the normalized value.

    Cast each color value into range 0 - 255, inclusive.
    If color is a str, return it unchanged.

    Warning: assumes color_range[0] <= color <= color_range[1]

    Args:
        color: The (R, G, B) color to normalize, or a string if invalid.
        color_range: The allowed min, max value of each component of color.

    Returns
        The normalized color, as a tuple of 3 ints, if color is sequence.
        The original value of color if color is a str.

    Raises:
        RuntimeError: if color is not a str and len(color) != 3
        RuntimeError: if len(color_range) != 2
        RuntimeError: if color_range[0] == color_range[1]
    """
    if len(color_range) != 2:
        raise RuntimeError(f"Invalid {color_range=}: must be a sequence of 2 numbers")
    if color_range[0] >= color_range[1]:
        raise RuntimeError(f"Invalid {color_range=}: max must be greater than min")
    if isinstance(color, str):
        return color
    if len(color) != 3:
        raise RuntimeError(
            f"Invalid {color=!r}: must be a sequence of length 3, or a str"
        )
    if min(color) < color_range[0] or max(color) > color_range[1]:
        raise RuntimeError(
            f"Invalid color {color=!r}: one or more elements out of range {color_range=}"
        )
    scale = 255 / (color_range[1] - color_range[0])
    return tuple(round((value - color_range[0]) * scale) for value in color)


def run_diff_weaving() -> None:
    """Command-line script to compare two pattern files."""
    parser = argparse.ArgumentParser(
        description="Compare two weaving pattern files and "
        "print differences in threading, picks, and thread colors. "
        "Either file may be in any supported format."
    )
    parser.add_argument("path1", type=pathlib.Path, help="File 1 to compare")
    parser.add_argument("path2", type=pathlib.Path, help="File 2 to compare")
    args = parser.parse_args()

    pattern1 = read_pattern_file(args.path1)
    pattern2 = read_pattern_file(args.path2)

    diff_strs = diff_patterns(pattern1=pattern1, pattern2=pattern2)

    for diff in diff_strs:
        print(diff)
    else:
        print("The patterns match")
