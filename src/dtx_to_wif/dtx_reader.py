__all__ = ["read_dtx"]

import re
from typing import TextIO

from .pattern_data import PatternData, WarpWeftData

UnitFiberSpacing = 0.053  # cm
DefaultIntSpacing = 4
DefaultFiberSpacing = UnitFiberSpacing * DefaultIntSpacing

DtxToWifSectionNames = {
    "color palet": "color table",
    "color palette": "color table",
}


class SectionData:
    """Raw data for a section of a pattern file.

    The fields are:
    • metadata: a dict of name: value (as a str, or None if no value)
    • data: a list of non-metadata values.
      Unless specified below, the data should a list of strings,
      one per line of data found in the file, with no processing.
    """

    def __init__(self) -> None:
        self.metadata: dict[str, str | None] = dict()
        self.data: list[str] = list()

    def add_line(self, line: str) -> None:
        if line.startswith("%%"):
            # Metadata is of the form {key}[ {value}]
            # (i.e. the value is optional)
            data = line[2:].split(None, maxsplit=1)
            key = data[0]
            value = data[1] if len(data) > 1 else None
            self.metadata[key] = value
        else:
            self.data.append(line)


def read_dtx(f: TextIO, filename: str = "?") -> PatternData:
    """Parse a dtx weaving file into PatternData

    Leading and trailing whitespace are stripped and blank lines are ignored.

    Args:
        f: The dtx file.
        filename: The file name. Usually ignored, but used as the pattern name
            if the dtx file does not have a "description" section.
    """
    # a dict of section name (each matching a field in PatternData):
    # data in PatternData format.
    sections = dict()
    section_name = ""
    for line in f:
        line = line.strip()
        if not line:
            continue

        if line.startswith("@@"):
            section_name = line[2:].strip().lower()
            section_name = DtxToWifSectionNames.get(section_name, section_name)
            section_name = section_name.replace(" ", "_")
            sections[section_name] = SectionData()
        else:
            sections[section_name].add_line(line)

    argdict = {}
    for section_name, processor in section_dispatcher.items():
        section_info = sections.get(section_name)
        if section_info is not None:
            argdict[section_name] = processor(section_info)
        else:
            argdict[section_name] = {}

    for ww_name in ("warp", "weft"):
        ww_colors: dict[int, int] | None = argdict.get(f"{ww_name}_colors")  # type: ignore
        if ww_colors:
            default_color: int | None = ww_colors[1]
        elif "color_table" in argdict:
            default_color = dict(warp=1, weft=2)[ww_name]
        else:
            default_color = None

        num_threads_name = dict(warp="ends", weft="picks")[ww_name]
        argdict[ww_name] = WarpWeftData(
            threads=int(get_metadata_item(sections, "info", num_threads_name, "0")),
            color=default_color,
            spacing=DefaultFiberSpacing,
            thickness=None,
            units="centimeters",
        )

    source_version = get_data_item(sections, "imprint", 0, "ignored ?").split()[1]
    if "." in source_version:
        # Drop everything after major.minor, if present,
        # to match what FiberWorks writes to WIF
        source_version = ".".join(source_version.split(".")[0:2])

    return PatternData(
        name=get_data_item(sections, "description", 0, filename),
        color_range=(0, 255),
        is_rising_shed=True,
        source_program="Fiberworks PCW",
        source_version=source_version,
        num_shafts=int(get_metadata_item(sections, "info", "shafts", "0")),
        num_treadles=int(get_metadata_item(sections, "info", "treadles", "0")),
        **argdict,  # type: ignore
    )


def process_color_table(section_info) -> dict[int, tuple[int, int, int]]:
    """Convert the color table (called color palete or color palette in dtx).

    Input format: one line per entry in the color table.
    Each entry is of the form "<r>,<g>,<b>" (e.g. "0,123,255")
    where each color is an int between 0 and 255.

    Output format: one line per entry in the color table.
    Each entry a tuple of 3 ints: r, g, b
    """
    result = {}
    for i, rgb_str in enumerate(section_info.data):
        rgb_tuple = tuple(int(value) for value in rgb_str.split(","))
        if len(rgb_tuple) != 3:
            raise RuntimeError(f"Color {i + 1}={rgb_str} invalid; not 3 ints:")
        result[i + 1] = rgb_tuple
    return result


def process_int_list(section_info) -> list[int]:
    """Process a section of space-separated ints

    The input data may be distributed over multiple lines,
    but the output will be a single list of ints.

    The output is a single list of ints.
    """

    section_data_str = " ".join(section_info.data)
    return [int(item) for item in section_data_str.split()]


def process_threading(section_info) -> dict[int, set[int]]:
    """Process the threading section.

    Note that WIF supports multiple shafts per thread,
    but dtx apparently does not.
    """
    intlist = process_int_list(section_info)
    return {thread + 1: {value} for thread, value in enumerate(intlist)}


def process_liftplan(liftplan_info) -> dict[int, set[int]]:
    """Process the liftplan section

    Input format: rows are picks, each a string of 0/1
    where 1 means lift the associated shaft

    Return: a dict of pick: tuple of shafts to raise,
    where pick and shafts are 1-based.
    """
    result = {}
    for pick, boolstr in enumerate(liftplan_info.data):
        result[pick + 1] = {i + 1 for i, value in enumerate(boolstr) if value == "1"}
    return result


def process_warpweft_colors(section_info) -> dict[int, int]:
    """Process a warp or weft colors section

    Input format: 0-based color indices into the color table
    as space-separated ints.

    Return colors as a dict of thread index: 0-based color index
    """
    int_values = process_int_list(section_info)
    return {i + 1: value + 1 for i, value in enumerate(int_values)}


def process_warpweft_spacing(section_info) -> dict[int, float]:
    """Process a warp or weft spacing section

    Input format: spacing as space-separated ints, each a multiple of
    UnitFiberSpacing = 0.053 cm

    Return spacing as a dict of thread index: spacing in cm
    """
    int_values = process_int_list(section_info)
    return {i + 1: value * UnitFiberSpacing for i, value in enumerate(int_values)}


def process_tieup(tieup_info) -> dict[int, set[int]]:
    """Process the tieup section.

    Input format: rows are shafts, with shaft 1 as the last line.
    Each row is string of 0 or 1 chars, of length # treadles

    Return a list of treadles, where each treadle is tuple of 1-based shafts.
    """
    result = {}
    num_treadles = len(tieup_info.data[0])
    for treadle in range(num_treadles):
        result[treadle + 1] = {
            i + 1
            for i, boolstr in enumerate(reversed(tieup_info.data))
            if boolstr[treadle] == "1"
        }
    return result


def process_treadling(treadling_info: SectionData) -> dict[int, set[int]]:
    """Process the treadling section.

    Input format:

    * Treadle numbers are 1-based
    * Treadle numbers for a given pick are separated by ", "
    * Treadle sets for each pick are separated by pure spaces

    Return:

    * 0-based treadle numbers (-1 means ignore this treadle).
    * Each line is a pick, a list of 1 or more treadles

    For example, if the compound treadling is as follows:

        pick 1: 1 3 4
        pick 2: 2
        pick 3: 1 4

    Then the input data is "1, 3, 4 2 1, 4"
    and the returned data is [(0, 2, 3), (1,), (0, 3)]
    """
    treadling_data_str = " ".join(treadling_info.data)
    # Delete spaces after commas, so we can split the resulting string
    # on spaces to obtain comma-separated sets of treadles
    compressed_treadling_data_str = re.sub(", +", ",", treadling_data_str)
    treadle_sets = compressed_treadling_data_str.split()
    return {
        pick + 1: {int(treadle) for treadle in treadle_set.split(",")}
        for pick, treadle_set in enumerate(treadle_sets)
    }


def process_notes(section_info: SectionData) -> dict[int, str]:
    """Process the notes section

    The input data is a list of strings.
    Return a dict of 1-based line number: string.
    """
    return {i + 1: line for i, line in enumerate(section_info.data)}


def get_data_item(
    data: dict[str, SectionData], section_name: str, index: int, default: str
) -> str:
    """Get one indexed element of SectionInfo.data.

    Args:
        data: Parsed dtx data; a dict of SectionInfo from parse_dtx_file.
        section_name: The name of the dtx section (lowercase).
        index: The index of the data item.
        default: The value to return if the section does not exist,
            or the index is out of range.
    """
    section_info = data.get(section_name)
    if section_info is None:
        return default
    if len(section_info.data) <= index:
        return default
    return section_info.data[index]


def get_metadata_item(
    data: dict[str, SectionData], section_name: str, name: str, default: str
) -> str:
    """Get one named element of SectionData.metadata as a str

    Args:
        data: Parsed dtx data; a dict of SectionInfo from parse_dtx_file.
        section_name: The name of the dtx section (lowercase).
        name: The name of the metadata item.
        default: The value to return if the section does not exists,
            the metadata does not exist, or the metadata has value None.
    """
    section_info = data.get(section_name)
    if section_info is None:
        return default
    result = section_info.metadata.get(name)
    if result is None:
        result = default
    return result


section_dispatcher = dict(
    threading=process_threading,
    tieup=process_tieup,
    treadling=process_treadling,
    liftplan=process_liftplan,
    color_table=process_color_table,
    warp_colors=process_warpweft_colors,
    weft_colors=process_warpweft_colors,
    warp_spacing=process_warpweft_spacing,
    weft_spacing=process_warpweft_spacing,
    notes=process_notes,
)
