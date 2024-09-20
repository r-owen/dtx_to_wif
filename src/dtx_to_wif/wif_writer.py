__all__ = ["write_wif"]

from typing import Any, TextIO

from .drawdown_data import DrawdownData


def as_wif_bool(value: Any) -> str:
    """Return "true" if bool(value), else "false"

    Used to create logical values that match the format FiberWorks uses
    when it writes WIF files.
    """
    return "true" if value else "false"


def write_wif(f: TextIO, data: DrawdownData) -> None:
    """Write a WIF file from parsed dtx data to the specified file.

    Parameters
    ----------
    f: file to write to, a writable file-like object
    data: parsed data
    """
    f.write(
        f"""[WIF]
Version=1.1
Date=April 20, 1997
Developers=wif@mhsoft.com
Source Program={data.source_program}
Source Version={data.source_version}

[CONTENTS]
COLOR PALETTE={as_wif_bool(data.color_table)}
TEXT=true
WEAVING=true
WARP={as_wif_bool(data.warp)}
WEFT={as_wif_bool(data.weft)}
COLOR TABLE=true
THREADING=true
TIEUP={as_wif_bool(data.tieup)}
TREADLING={as_wif_bool(data.treadling)}
LIFTPLAN={as_wif_bool(data.liftplan)}
WARP COLORS={as_wif_bool(data.warp_colors)}
WEFT COLORS={as_wif_bool(data.weft_colors)}
WARP SPACING={as_wif_bool(data.warp_spacing)}
WEFT SPACING={as_wif_bool(data.weft_spacing)}
WARP THICKNESS={as_wif_bool(data.warp_thickness)}
WEFT THICKNESS={as_wif_bool(data.weft_thickness)}

[TEXT]
Title={data.name}
"""
    )

    # Write WARP COLORS, WEFT COLORS
    for name in ("warp", "weft"):
        colors = getattr(data, f"{name}_colors")
        if colors:
            f.write(f"\n[{name.upper()} COLORS]\n")
            for thread, color in colors.items():
                f.write(f"{thread}={color}\n")

    # Write WARP SPACING, WARP THICKNESS, WEFT SPACING, WEFT THICKNESS
    for name in ("warp", "weft"):
        for what in ("spacing", "thickness"):
            value_dict = getattr(data, f"{name}_{what}")
            if value_dict:
                f.write(f"\n[{name.upper()} {what.upper()}]\n")
                for thread, value in value_dict.items():
                    f.write(f"{thread}={value:0.3f}\n")

    f.write("\n[THREADING]\n")
    for thread, shafts in data.threading.items():
        shafts_str = ",".join(str(shaft) for shaft in shafts)
        f.write(f"{thread}={shafts_str}\n")

    if data.tieup:
        f.write("\n[TIEUP]\n")
        for treadle, shafts in data.tieup.items():
            shafts_str = ",".join(str(shaft) for shaft in shafts)
            f.write(f"{treadle}={shafts_str}\n")

    if data.treadling:
        f.write("\n[TREADLING]\n")
        for thread, treadles in data.treadling.items():
            treadle_str = ",".join(str(treadle) for treadle in treadles)
            f.write(f"{thread}={treadle_str}\n")

    if data.liftplan:
        f.write("\n[LIFTPLAN]\n")
        for thread, shafts in data.liftplan.items():
            shafts_str = ",".join(str(shaft) for shaft in shafts)
            f.write(f"{thread}={shafts_str}\n")

    f.write(
        f"""
[WEAVING]
Rising Shed={as_wif_bool(data.is_rising_shed)}
Treadles={data.num_treadles}
Shafts={data.num_shafts}
"""
    )

    # Write WARP and WEFT
    for name in ("warp", "weft"):
        ww_data = getattr(data, name)
        f.write(f"\n[{name.upper()}]\n")
        f.write(f"Threads={ww_data.threads}\n")
        if ww_data.color is not None:
            # color can have 1 or 4 values
            # the first is always the color index
            # the remaining are the three color_rgb values, if present
            color_values = [ww_data.color]
            if ww_data.color_rgb is not None:
                color_values.append(ww_data.color_rgb)
            valuestr = ",".join(str(value) for value in color_values)
            f.write(f"Color={valuestr}\n")
        if ww_data.spacing is not None:
            f.write(f"Spacing={ww_data.spacing:0.3f}\n")
        if ww_data.thickness is not None:
            f.write(f"Thickness={ww_data.thickness:0.3f}\n")
        if ww_data.units is not None:
            f.write(f"Units={ww_data.units}\n")

    if data.color_table:
        f.write("\n[COLOR TABLE]\n")
        for color_index, rgbcolors in data.color_table.items():
            if len(rgbcolors) != 3:
                raise RuntimeError(
                    f"Cannot parse COLOR TABLE item {color_index}={rgbcolors}; "
                    "the color is not 3 comma-separated integers"
                )
            if min(rgbcolors) < 0 or max(rgbcolors) > 255:
                raise RuntimeError("One or more color values out of range 0-255")
            color_str = ",".join(str(color) for color in rgbcolors)
            f.write(f"{color_index}={color_str}\n")

        if data.color_range is not None:
            f.write(
                f"""
[COLOR PALETTE]
Range={data.color_range[0]},{data.color_range[1]}
Entries={len(data.color_table)}
"""
            )
