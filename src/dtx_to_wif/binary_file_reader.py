from typing import BinaryIO


class BinaryFileReader:
    """A binary file reader.

    Args:
        f: The file to read.
        big_endian: Is most data big-endian?
            Used as the default for reading integers.
    """

    def __init__(self, f: BinaryIO, big_endian: bool):
        self.f = f
        self.big_endian = big_endian

    def read_bytes(self, num_bytes: int) -> bytes:
        """Read exactly num_bytes bytes (possibly using multiple reads).

        Raises:
            EOFError: If EOF seen.
            ValueError: If num_bytes < 1.
        """
        if num_bytes < 1:
            raise ValueError("{num_bytes=} must be positive")
        data = b""
        while True:
            new_data = self.f.read(num_bytes - len(data))
            if len(new_data) == 0:
                raise EOFError("File too short")
            data += new_data
            if len(data) == num_bytes:
                return data
            elif len(data) > num_bytes:
                raise RuntimeError("Bug! read {len(data)} bytes > {num_bytes=}")

    def read_int(
        self, *, num_bytes: int, signed: bool, big_endian: bool | None = None
    ) -> int:
        """Read num_bytes bytes as a signed or unsigned integer.

        Args:
            num_bytes: The number of bytes to read.
            signed: Is the integer be signed?
            big_endian: Is the integer big-endian? Specify None for default.
        """
        data = self.read_bytes(num_bytes)
        if big_endian is None:
            big_endian = self.big_endian
        result = int.from_bytes(
            data, byteorder="big" if big_endian else "little", signed=signed
        )
        return result

    def read_int8(self, big_endian: bool | None = None) -> int:
        """Read a 1-byte signed int.

        Args:
            big_endian: Is the integer big-endian? Specify None for default.
        """
        return self.read_int(num_bytes=1, signed=True, big_endian=big_endian)

    def read_int16(self, big_endian: bool | None = None) -> int:
        """Read a 2-byte signed int.

        Args:
            big_endian: Is the integer big-endian? Specify None for default.
        """
        return self.read_int(num_bytes=2, signed=True, big_endian=big_endian)

    def read_int32(self, big_endian: bool | None = None) -> int:
        """Read a 4-byte signed int.

        Args:
            big_endian: Is the integer big-endian? Specify None for default.
        """
        return self.read_int(num_bytes=4, signed=True, big_endian=big_endian)

    def read_uint8(self, big_endian: bool | None = None) -> int:
        """Read a 1-byte unsigned int.

        Args:
            big_endian: Is the integer big-endian? Specify None for default.
        """
        return self.read_int(num_bytes=1, signed=False, big_endian=big_endian)

    def read_uint16(self, big_endian: bool | None = None) -> int:
        """Read a 2-byte unsigned int.

        Args:
            big_endian: Is the integer big-endian? Specify None for default.
        """
        return self.read_int(num_bytes=2, signed=False, big_endian=big_endian)

    def read_uint32(self, big_endian: bool | None = None) -> int:
        """Read a 4-byte unsigned int.

        Args:
            big_endian: Is the integer big-endian? Specify None for default.
        """
        return self.read_int(num_bytes=4, signed=False, big_endian=big_endian)
