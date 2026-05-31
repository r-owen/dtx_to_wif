import copy
import unittest

from dtx_to_wif import PatternData, WarpWeftData, diff_patterns, make_liftplan

# Use deep copies of this pattern in the tests.
# Deep copies allow the test to modify one pattern
# without affecting the other pattern to which it is being compared.
_Pattern = PatternData(
    name="many color multiple treadles and zeros.dtx",
    threading={1: {2}, 2: {3}, 3: {4}, 5: {1}},
    tieup={1: {1, 3}, 2: {2, 4}, 3: {1}, 4: {2}, 5: {3}, 6: {4}},
    treadling={1: {1, 6}, 2: {5}, 3: {2, 3, 4}, 4: {0, 1, 4}, 5: {5, 6}, 6: {3}},
    liftplan={},
    color_table={
        1: (255, 255, 255),
        2: (255, 0, 0),
        3: (0, 255, 0),
        4: (0, 0, 255),
        6: (0, 0, 0),
        5: (170, 170, 170),
        7: (255, 255, 15),
        8: (255, 20, 255),
        9: (30, 255, 255),
        10: (150, 50, 255),
    },
    warp=WarpWeftData(
        threads=5,
        color=3,
        color_rgb=None,
        spacing=0.212,
        thickness=0.103,
        units="Centimeters",
    ),
    weft=WarpWeftData(
        threads=6,
        color=8,
        color_rgb=None,
        spacing=0.036,
        thickness=0.051,
        units="Inches",
    ),
    warp_colors={2: 4, 3: 5, 4: 1, 5: 2},
    warp_spacing={2: 0.159, 3: 0.106, 4: 0.053},
    warp_thickness={2: 0.111, 3: 0.055, 4: 0.13},
    weft_colors={2: 9, 3: 10, 4: 6, 5: 7},
    weft_spacing={1: 0.053, 2: 0.106, 3: 0.159, 5: 0.265, 6: 0.318},
    weft_thickness={1: 0.032, 2: 0.054, 3: 0.089, 5: 0.111, 6: 0.099},
    color_range=(0, 255),
)


def get_pattern() -> PatternData:
    return copy.deepcopy(_Pattern)


class TestDiffPatterns(unittest.TestCase):
    def test_identity(self):
        pattern1 = get_pattern()
        pattern2 = get_pattern()
        assert diff_patterns(pattern1, pattern2) == []

    def test_color(self):
        # Delete non-default colors
        for warp_weft in ("warp", "weft"):
            pattern1 = get_pattern()
            pattern2 = get_pattern()
            color_dict1 = getattr(pattern1, f"{warp_weft}_colors")
            num_non_default_colors1 = len(color_dict1)
            non_default_color_threads = set(color_dict1.keys())
            while non_default_color_threads:
                thread = non_default_color_threads.pop()
                del color_dict1[thread]
                expected_len = num_non_default_colors1 - len(non_default_color_threads)
                assert len(diff_patterns(pattern1, pattern2)) == expected_len
                assert len(diff_patterns(pattern2, pattern1)) == expected_len
            assert color_dict1 == {}

        # Change thread colors to a value not used in the pattern
        for warp_weft in ("warp", "weft"):
            pattern1 = get_pattern()
            pattern2 = get_pattern()
            color_dict1 = getattr(pattern1, f"{warp_weft}_colors")
            unused_color = (1, 2, 3)
            for color in color_dict1.values():
                assert color != unused_color
            for i, thread in enumerate(color_dict1):
                color_dict1[thread] = unused_color
                expected_len = i + 1
                assert len(diff_patterns(pattern1, pattern2)) == expected_len
                assert len(diff_patterns(pattern2, pattern1)) == expected_len

    def test_liftplan(self):
        pattern1 = get_pattern()
        pattern2 = get_pattern()
        pattern1.liftplan = make_liftplan(pattern1)
        pattern2.liftplan = make_liftplan(pattern2)

        assert diff_patterns(pattern1, pattern2) == []

        # Test deletion of picks
        num_picks2 = len(pattern2.liftplan)
        picks1 = set(pattern1.liftplan.keys())
        while picks1:
            pick = picks1.pop()
            del pattern1.liftplan[pick]
            if picks1:
                # The liftplan still exists.
                # +1 because the number of picks differs.
                expected_len = 1 + num_picks2 - len(picks1)
            else:
                # The liftplan is empty, so threading is used,
                # and the threading matches the liftplan.
                expected_len = 0
            assert len(diff_patterns(pattern1, pattern2)) == expected_len
            assert len(diff_patterns(pattern2, pattern1)) == expected_len
        assert pattern1.liftplan == {}

        # Test modification of picks
        for i, shaft_set in enumerate(pattern1.liftplan.values()):
            if 1 not in shaft_set:
                shaft_set |= {1}
            else:
                shaft_set.pop()
            expected_len = i + 1
            assert len(diff_patterns(pattern1, pattern2)) == expected_len
            assert len(diff_patterns(pattern2, pattern1)) == expected_len

    def test_liftplan_vs_treadling(self):
        pattern1 = get_pattern()
        pattern2 = get_pattern()
        pattern2.liftplan = make_liftplan(pattern1)

        # Test that liftplan matches treadling
        assert diff_patterns(pattern1, pattern2) == []

        # Test that liftplan is higher priority than tieup or treadling
        pattern2.tieup = {1: {1}}
        assert diff_patterns(pattern1, pattern2) == []

        pattern2.tieup = pattern1.tieup
        pattern2.treadling = {1: {1}}
        assert diff_patterns(pattern1, pattern2) == []

        pattern2.tieup = {}
        pattern2.treadling = {}
        assert diff_patterns(pattern1, pattern2) == []

        del pattern2.liftplan[1]
        assert len(diff_patterns(pattern1, pattern2)) == 2

        del pattern2.liftplan[3]
        assert len(diff_patterns(pattern1, pattern2)) == 3

    def test_threading(self):
        pattern1 = get_pattern()
        pattern2 = get_pattern()
        num_picks2 = len(pattern2.threading)

        # Test deleting ends
        picks1 = set(pattern1.threading.keys())
        while picks1:
            pick = picks1.pop()
            del pattern1.threading[pick]
            # +1 because the number if ends differs.
            expected_len = 1 + num_picks2 - len(picks1)
            assert len(diff_patterns(pattern1, pattern2)) == expected_len
            assert len(diff_patterns(pattern2, pattern1)) == expected_len
        assert pattern1.threading == {}

        # Test changing ends
        pattern1 = get_pattern()
        pattern2 = get_pattern()

        for i, shaft_set in enumerate(pattern1.threading.values()):
            if 1 not in shaft_set:
                shaft_set |= {1}
            else:
                shaft_set.pop()
            expected_len = i + 1
            assert len(diff_patterns(pattern1, pattern2)) == expected_len
            assert len(diff_patterns(pattern2, pattern1)) == expected_len

    def test_treadling(self):
        pattern1 = get_pattern()
        pattern2 = get_pattern()

        # Test deleting picks.
        num_threads2 = len(pattern2.treadling)
        threads1 = set(pattern1.treadling.keys())
        while threads1:
            thread = threads1.pop()
            del pattern1.treadling[thread]
            # +1 because the number if picks differs.
            expected_len = 1 + num_threads2 - len(threads1)
            assert len(diff_patterns(pattern1, pattern2)) == expected_len
            assert len(diff_patterns(pattern2, pattern1)) == expected_len
        assert pattern1.treadling == {}

        # Test changing picks. The difficulty is that changing the treadles
        # for a pick doesn't automatically change the resulting shaft set.
        # To fix this, change the patterns to use a liftplan-like tieup.
        # This requires redoing the treadling to limit the treadles to
        # the shaft numbers. Warning: the new treadling must not have shaft 0,
        # since popping that has no effect on the shafts raised.
        assert pattern1.num_shafts == 4
        tieup = {i: {i} for i in range(1, pattern1.num_shafts + 1)}
        treadling = {1: {1, 4}, 2: {3}, 3: {2, 3, 4}, 4: {1, 4}, 5: {2, 4}, 6: {3}}
        pattern1.tieup = tieup
        pattern2.tieup = tieup
        pattern1.treadling = copy.deepcopy(treadling)
        pattern2.treadling = copy.deepcopy(treadling)

        for i, shaft_set in enumerate(pattern1.treadling.values()):
            if 1 not in shaft_set:
                shaft_set |= {1}
            else:
                shaft_set.pop()
            expected_len = i + 1
            assert len(diff_patterns(pattern1, pattern2)) == expected_len
            assert len(diff_patterns(pattern2, pattern1)) == expected_len


if __name__ == "__main__":
    unittest.main()
