from __future__ import annotations

__all__ = ["PatternData", "TreadlingType", "WarpWeftData"]

import dataclasses
import enum
import warnings
from typing import Any, TypeVar

ValueType = TypeVar("ValueType")


class TreadlingType(enum.Enum):
    SingleTreadle = enum.auto()
    MultiTreadle = enum.auto()
    Liftplan = enum.auto()


@dataclasses.dataclass
class WarpWeftData:
    """Information for the WARP or WEFT sections of a WIF file.

    Args:
        threads: The number of threads. PatternData increases the value,
            if needed, so the default value of 0 results in
            the minimum required to satisfy the weaving pattern.
        color: Default color index (index into color table).
        color_rgb: Default color as r,g,b.
        spacing: Default thread spacing.
        thickness: Default thread thickness.
        units: Inits for spacing and thickness.
    """

    threads: int = 0
    color: int | None = None
    color_rgb: tuple[int, int, int] | None = None
    spacing: float | None = None
    thickness: float | None = None
    units: str | None = None


@dataclasses.dataclass
class PatternData:
    """Data for a weaving pattern.

    The contents and format are intended to match the WIF specification.
    Thus indices are 1-based.

    Note that 0 is the standard value for "does not exist" or "does nothing".
    For example shaft 0 holds no warp threads and treadle 0 lifts no shafts.

    Args:
        name: Original file name.
        threading: Dict of thread index: shafts,
            where shaft is a set of shafts.
            Omitted entries are not threaded on any shaft.
            The values are sets of integers, instead of single integers,
            because WIF supports threading on more than one shaft.
        tieup: Dict of treadle: shaft set.
            Omitted entries raise no shafts.
        treadling: Dict of pick index: treadle set.
            Omitted entries raise no shafts.
        liftplan: Dict of pick index: shafts where shafts is a set
            of 1-based shafts. Omitted picks lift nothing.
            Omitted entries raise no shafts.
        color_table: Dict of color index: color tuple,
            where each color is a tuple of (r, g, b) values.
            The keys must include all integers from 1 through len(color_table).
        warp: Warp data; see WarpWeftData.
        weft: Weft data; see WarpWeftData.
        warp_colors: Color for each warp thread,
            as a dict of thread index: index into color_table.
        warp_spacing: Space each thread takes up,
            as a dict of thread index: spacing.
        warp_thickness: Thickness of each thread,
            as a dict of thread index: thickness.
        weft_colors: Color for each weft thread,
            as a dict of thread index: index into color_table.
        weft_spacing: Space each thread takes up,
            as a dict of thread index: spacing.
        weft_thickness: Thickness of each thread,
            as a dict of thread index: thickness.
        color_range: Minimum, maximum allowed color value (inclusive).
        is_rising_shed: If true, shafts go up, if false, shafts go down.
        source_program: Name of program that wrote the original file.
        source_version: Version of pogram that wrote the original file.
        num_shafts: Number of shafts.
        num_treadles: Number of treadles.

    Note:
        Many fields are cleaned up in postprocessing:

        *  `num_shafts` and `num_treadles` are increased, if needed,
          based on computation from `threading`, `tieup`, `treadling`,
          and `liftplan`. Thus you can set each of these to 0 (the default)
          to have them set to the smallest value required. The only reason to
          specify a value larger than the actual number of shafts or treadles
          is as a placeholder for an incomplete weaving pattern--one you are
          working on and have not yet provided all threadings or treadlings.

        * Warp/weft colors, `spacing`, and `thickness` have keys
          sorted, and default values are deleted.

        * `color_table` has keys sorted.

        * `threading`, `tieup`, `treadling`, and `liftplan` have their
          keys sorted in ascending order.
          Also entries with value `{}` or `{0}` are removed,
          since those values mean the same thing as no entry.
          However, 0 is not removed from sets containing other values.

        * If `warp` or `weft`

    Raises:
        RuntimeError: If there is missing treadling information. The data must
            either include both of tieup and treadling, or else liftplan.
        RuntimeError: If there are more treadles in treadling than in tieup.
            If any color values are out of range.
        RuntimeError: If the color keys are not a complete set 1, 2, ... N
            (though they don't have to sorted on input).
        RuntimeError: If `warp_colors` or `weft_colors` is specified,
            but not `color_table`.
        RuntimeError: If `color_table` is specified, but not `color_range`.
        RuntimeError: If `color_range` invalid: length != 2 or
            color_range[0] (min) >= color_range[1] (max)
        RuntimeError: If any color value is out of range, with one exception:
            if warp/weft.color is out of range, but every warp/weft thread
            specifies a valid color, then issue a RuntimeWarning
            and set warp/weft.color to the color of the first warp/weft thread.

    """

    name: str
    threading: dict[int, set[int]]
    tieup: dict[int, set[int]]
    treadling: dict[int, set[int]]
    liftplan: dict[int, set[int]]
    color_table: dict[int, tuple[int, int, int]]
    warp: WarpWeftData
    weft: WarpWeftData
    warp_colors: dict[int, int] = dataclasses.field(default_factory=dict)
    warp_spacing: dict[int, float] = dataclasses.field(default_factory=dict)
    warp_thickness: dict[int, float] = dataclasses.field(default_factory=dict)
    weft_colors: dict[int, int] = dataclasses.field(default_factory=dict)
    weft_spacing: dict[int, float] = dataclasses.field(default_factory=dict)
    weft_thickness: dict[int, float] = dataclasses.field(default_factory=dict)
    color_range: tuple[int, int] | None = None
    is_rising_shed: bool = True
    source_program: str = "?"
    source_version: str = "?"
    num_shafts: int = 0
    num_treadles: int = 0

    def __post_init__(self) -> None:
        # Test for missing color table before cleaning warp and weft colors
        # since they may well be empty afterwards
        if self.warp_colors or self.weft_colors:
            if not self.color_table:
                raise RuntimeError(
                    "warp and/or weft colors specified, but not color table"
                )

        # Clean up warp/weft colors, spacing, and threading dicts
        # Put the keys in thread order and elide default values (if known).
        for ww in ("warp", "weft"):
            for field_name in ("colors", "spacing", "thickness"):
                # The default color name has no final s; all other names match
                default_name = {"colors": "color"}.get(field_name, field_name)
                dict_name = f"{ww}_{field_name}"
                default_class = getattr(self, ww, None)
                if default_class is not None:
                    default_value = getattr(default_class, f"{default_name}")
                else:
                    default_value = None
                setattr(
                    self,
                    dict_name,
                    self._clean_dict(getattr(self, dict_name), default_value),
                )

        # Clean up the threading, tieup, treadling, and liftplan dicts
        # by putting keys in order and eliding default values
        self.threading = self._clean_ints_set_dict(self.threading)
        self.tieup = self._clean_ints_set_dict(self.tieup)
        self.treadling = self._clean_ints_set_dict(self.treadling)
        self.liftplan = self._clean_ints_set_dict(self.liftplan)

        # Clean up the color_table, which has no default values
        self.color_table = self._clean_dict(self.color_table, dataclasses._MISSING_TYPE)

        self.warp.threads = max(len(self.threading), self.warp.threads)

        # Preliminary estimate
        max_shaft_in_threading = max(max(shafts) for shafts in self.threading.values())
        self.num_shafts = max(max_shaft_in_threading, self.num_shafts)

        # Favor tieup + treadling over liftplan
        # since it is easy to convert to liftplan, but not back again
        if self.tieup and self.treadling:
            # There may be shafts in the tieup that were not threaded
            max_shafts_in_liftplan_in_tieup = max(
                len(shafts) for shafts in self.tieup.values()
            )
            self.num_shafts = max(max_shafts_in_liftplan_in_tieup, self.num_shafts)
            self.num_treadles = max(len(self.tieup), self.num_treadles)

            max_num_treadles_per_pick = max(
                len(treadles) for treadles in self.treadling.values()
            )
            if max_num_treadles_per_pick == 1:
                self.treadling_type = TreadlingType.SingleTreadle
            else:
                self.treadling_type = TreadlingType.MultiTreadle
            self.weft.threads = max(len(self.treadling), self.weft.threads)

            max_treadle_ind_from_treadling = max(
                max(treadles) for treadles in self.treadling.values()
            )
            if self.num_treadles < max_treadle_ind_from_treadling:
                raise RuntimeError(
                    "Found more treadles in treadling than in tieup: "
                    f"{self.num_treadles} > {max_treadle_ind_from_treadling}"
                )

        elif self.liftplan:
            self.treadling_type = TreadlingType.Liftplan
            # There may be shafts in the liftplan that were not in the tieup
            max_shafts_in_liftplan = max(
                max(shafts) for shafts in self.liftplan.values()
            )
            self.num_shafts = max(max_shafts_in_liftplan, self.num_shafts)

            self.num_treadles = max(self.num_shafts, self.num_treadles)
            self.weft.threads = max(len(self.liftplan), self.weft.threads)

        else:
            raise RuntimeError(
                "Must specify non-empty liftplan, or both tieup and treadling"
            )

        if self.color_table and self.color_range is None:
            raise RuntimeError("color table specified, but not color range")

        if self.color_range is not None:
            if len(self.color_range) != 2:
                raise RuntimeError(
                    f"Invalid color range={self.color_range}; must be two values"
                )

            if self.color_range[0] >= self.color_range[1]:
                raise RuntimeError(
                    f"Invalid color range={self.color_range}; min must be < max"
                )

            if self.color_table:
                if list(self.color_table.keys()) != list(
                    range(1, len(self.color_table) + 1)
                ):
                    raise RuntimeError(
                        f"Color table keys {list(self.color_table.keys())} "
                        f"not 1, 2, ... {len(self.color_table)}"
                    )
                for i, color_rgb in self.color_table.items():
                    if (
                        min(color_rgb) < self.color_range[0]
                        or max(color_rgb) > self.color_range[1]
                    ):
                        raise RuntimeError(
                            f"color table entry {i}={color_rgb} invalid: "
                            f"one or more values not in range "
                            f"[{self.color_range[0]}, {self.color_range[1]}]"
                        )

        # Check that all color values are in range
        max_color_in_table = max(self.color_table.keys())
        for ww_name in ("warp", "weft"):
            ww_colors = getattr(self, f"{ww_name}_colors")
            if ww_colors:
                if max(ww_colors.values()) > max_color_in_table:
                    raise RuntimeError(
                        f"Invalid {ww_name}_colors={ww_colors}: "
                        f"one or more colors > {max_color_in_table}; "
                    )
                if min(getattr(self, f"{ww_name}_colors").values()) < 1:
                    raise RuntimeError(
                        f"Invalid {ww_name}_colors={ww_colors}: one or more colors < 1"
                    )
            ww_info = getattr(self, ww_name)
            if ww_info.color is not None:
                if ww_info.color < 1 or ww_info.color > max_color_in_table:
                    errmsg = f"Invalid {ww_name}.color {ww_info.color} not in range [0, {max_color_in_table}]"
                    if ww_colors.keys() == set(range(1, 1 + len(ww_colors))):
                        # The invalid default color is not actually used,
                        # so rather than reject the file,
                        # warn and change the default color to something valid.
                        warnings.warn(
                            f"{errmsg}: changing to a valid value and continuing",
                            category=RuntimeWarning,
                        )
                        ww_info.color = ww_colors[1]
                    else:
                        raise RuntimeError(errmsg)

    def _clean_dict(
        self, data: dict[int, ValueType], default_value: Any
    ) -> dict[int, ValueType]:
        """Sort by keys and remove default entries.

        Use a default value of dataclasses.dataclasses._MISSING_TYPE,
        or similar, if the dict has no default values.
        """
        return {key: data[key] for key in sorted(data) if data[key] != default_value}

    def _clean_ints_set_dict(self, data: dict[int, set[int]]) -> dict[int, set[int]]:
        """Sort by keys and remove items with default value ({} or {0})."""
        return {key: data[key] for key in sorted(data) if bool(data[key] - {0})}
