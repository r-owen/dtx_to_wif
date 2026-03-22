import io
import itertools
import unittest

from dtx_to_wif import BinaryFileReader

uint8s = [0xFF, 0xEF, 0x1F, 0xF, 1, 0]
uint16s = [0xFFFF, 0xEFFF, 0x1FFF, 0xFFF, 0xEFF, 0x1FF, *uint8s]
uint24s = [0xFFFFFF, 0xEFFFFF, 0x1FFFFF, 0xFFFFF, 0xEFFFF, 0x1FFFF, *uint16s]
uint32s = [
    0xFFFFFFFF,
    0xEFFFFFFF,
    0x1FFFFFFF,
    0xFFFFFFF,
    0xEFFFFFF,
    0x1FFFFFF,
    *uint24s,
]
int8s = [-128, -127 - 1, 0, 1, 126, 127]
int16s = [-32_768, 32_766, *int8s]
int32s = [-2_147_483, 648, 2_147_483_647, *int16s]


class TestBinaryFileReader(unittest.TestCase):
    def int_iterator(self):
        """Get an endless int iterator for all types of ints.

        Each iteration returns 7 values:
            big_endian, uint8, uint16, uint32, int8, int16, int32
        """
        value_iter = zip(
            itertools.cycle([False, True]),
            itertools.cycle(uint8s),
            itertools.cycle(uint16s),
            itertools.cycle(uint32s),
            itertools.cycle(int8s),
            itertools.cycle(int16s),
            itertools.cycle(int32s),
        )
        for _ in range(len(uint32s)):
            yield next(value_iter)

    def test_read_bytes(self) -> None:
        bytes_data = b"some bytes\0 and more bytes\0\1"
        with io.BytesIO(initial_bytes=bytes_data) as f:
            bfr = BinaryFileReader(
                f, big_endian=False
            )  # big_endian value is irrelevant for this test
            with self.assertRaises(ValueError):
                bfr.read_bytes(num_bytes=-1)
            read_bytes = bfr.read_bytes(num_bytes=len(bytes_data))
            assert read_bytes == bytes_data
            with self.assertRaises(EOFError):
                bfr.read_bytes(num_bytes=1)

    def test_read_int(self) -> None:
        with io.BytesIO() as f:
            for (
                big_endian,
                uint8,
                uint16,
                uint32,
                int8,
                int16,
                int32,
            ) in self.int_iterator():
                byteorder = "big" if big_endian else "little"
                f.write(uint8.to_bytes(length=1, byteorder=byteorder, signed=False))
                f.write(uint16.to_bytes(length=2, byteorder=byteorder, signed=False))
                f.write(uint32.to_bytes(length=4, byteorder=byteorder, signed=False))
                f.write(int8.to_bytes(length=1, byteorder=byteorder, signed=True))
                f.write(int16.to_bytes(length=2, byteorder=byteorder, signed=True))
                f.write(int32.to_bytes(length=4, byteorder=byteorder, signed=True))
            f.flush()
            written_bytes = f.getvalue()

        # Read and check the data using explicit big_endian
        with io.BytesIO(initial_bytes=written_bytes) as f:
            bfr = BinaryFileReader(
                f, big_endian=False
            )  # big_endian value is ignored for this test
            for (
                big_endian,
                uint8,
                uint16,
                uint32,
                int8,
                int16,
                int32,
            ) in self.int_iterator():
                assert bfr.read_uint8(big_endian=big_endian) == uint8
                assert bfr.read_uint16(big_endian=big_endian) == uint16
                assert bfr.read_uint32(big_endian=big_endian) == uint32
                assert bfr.read_int8(big_endian=big_endian) == int8
                assert bfr.read_int16(big_endian=big_endian) == int16
                assert bfr.read_int32(big_endian=big_endian) == int32

        # Read and check with default big_endian (when possible)
        for default_big_endian in (False, True):
            with io.BytesIO(initial_bytes=written_bytes) as f:
                bfr = BinaryFileReader(f, big_endian=default_big_endian)
                for (
                    big_endian,
                    uint8,
                    uint16,
                    uint32,
                    int8,
                    int16,
                    int32,
                ) in self.int_iterator():
                    be_arg = None if big_endian == default_big_endian else big_endian
                    assert bfr.read_uint8(big_endian=be_arg) == uint8
                    assert bfr.read_uint16(big_endian=be_arg) == uint16
                    assert bfr.read_uint32(big_endian=be_arg) == uint32
                    assert bfr.read_int8(big_endian=be_arg) == int8
                    assert bfr.read_int16(big_endian=be_arg) == int16
                    assert bfr.read_int32(big_endian=be_arg) == int32


if __name__ == "__main__":
    unittest.main()
