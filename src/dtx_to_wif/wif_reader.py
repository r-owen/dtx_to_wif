__all__ = ["read_wif"]

import warnings
from configparser import ConfigParser, SectionProxy
from typing import TextIO

from .drawdown_data import DrawdownData, WarpWeftData

# Valid WIF bool string values (cast to lowercase)
# and associated bool value
WifBoolDict = {
    "true": True,
    "on": True,
    "yes": True,
    "1": True,
    "false": False,
    "off": False,
    "no": False,
    "0": False,
}


def read_wif(f: TextIO) -> DrawdownData:
    """Parse a dtx weaving file into DrawdownData

    Leading and trailing whitespace are stripped
    and blank lines are ignored.
    """
    raw_data = ConfigParser()
    raw_data.read_file(f)

    # Change section names to lowercase and " " to "_"
    # (this is harder than it should be)
    for old_section_name in raw_data.sections():
        new_section_name = old_section_name.lower().replace(" ", "_")
        if new_section_name != old_section_name:
            raw_data.add_section(new_section_name)
            for key, value in raw_data.items(old_section_name):
                raw_data.set(new_section_name, key, value)
            raw_data.remove_section(old_section_name)

    parsed_data = {}
    for section_name, processor in section_dispatcher.items():
        if raw_data.has_section(section_name):
            section = raw_data[section_name]
            parsed_data[section_name] = processor(section)
        else:
            parsed_data[section_name] = []

    for wwname in ("warp", "weft"):
        colorstr = raw_data.get(wwname, "color", fallback=None)
        if colorstr:
            # Format is either 1 int (color index)
            # or 4 ints (color index, r, g, b)
            # Any other length is treated as 1, with a warning
            colorvalues = [int(value) for value in colorstr.split(",")]
            if len(colorvalues) not in (1, 4):
                warnings.warn(
                    f"{wwname.upper()}: color={colorstr} should have 1 or 4 ints; "
                    "ignoring all but first value"
                )
            color = colorvalues[0]
            color_rgb = tuple(colorvalues[1:4]) if len(colorvalues) == 4 else None
        else:
            color = None
            color_rgb = None
        parsed_data[wwname] = WarpWeftData(
            threads=raw_data.getint(wwname, "threads", fallback=0),
            color=color,
            color_rgb=color_rgb,  # type: ignore
            spacing=raw_data.getfloat(wwname, "spacing", fallback=None),
            thickness=raw_data.getfloat(wwname, "thickness", fallback=None),
            units=raw_data.get(wwname, "units", fallback=None),
        )

    color_range_str = raw_data.get("color_palette", "range", fallback=None)
    if color_range_str is not None:
        color_range = tuple(int(value) for value in color_range_str.split(","))
        if len(color_range) != 2:
            raise RuntimeError(
                f"COLOR PALETTE: RANGE {color_range} must contain two values"
            )

    return DrawdownData(
        name=raw_data.get("text", "title", fallback="?"),
        color_range=color_range,  # type: ignore
        is_rising_shed=raw_data.getboolean("weaving", "rising shed", fallback=True),
        source_program=raw_data.get("wif", "source program", fallback="?"),
        source_version=raw_data.get("wif", "source version", fallback="?"),
        num_shafts=raw_data.getint("weaving", "shafts", fallback=0),
        num_treadles=raw_data.getint("weaving", "treadles", fallback=0),
        **parsed_data,  # type: ignore
    )


def process_as_dict_of_int(section: SectionProxy) -> dict[int, int]:
    """Process as a dict of int: int"""
    return {int(key): int(value) for key, value in section.items()}


def process_as_dict_of_int_tuples(section: SectionProxy) -> dict[int, tuple[int, ...]]:
    """Process as a dict of tuples of ints."""
    return {
        int(key): tuple(int(shaft) for shaft in value.split(","))
        for key, value in section.items()
    }


def process_as_dict_of_float(section: SectionProxy) -> dict[int, float]:
    """Process as a dict of int str: float str"""
    return {int(key): float(value) for key, value in section.items()}


section_dispatcher = dict(
    threading=process_as_dict_of_int_tuples,
    tieup=process_as_dict_of_int_tuples,
    treadling=process_as_dict_of_int_tuples,
    liftplan=process_as_dict_of_int_tuples,
    color_table=process_as_dict_of_int_tuples,
    warp_colors=process_as_dict_of_int,
    weft_colors=process_as_dict_of_int,
    warp_spacing=process_as_dict_of_float,
    weft_spacing=process_as_dict_of_float,
    warp_thickness=process_as_dict_of_float,
    weft_thickness=process_as_dict_of_float,
)
