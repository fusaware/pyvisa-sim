from typing import List, Optional

import pytest

from pyvisa_sim import common


@pytest.mark.parametrize(
    "bits, want",
    [
        (0, 0b0),
        (1, 0b1),
        (5, 0b0001_1111),
        (7, 0b0111_1111),
        (8, 0b1111_1111),
        (11, 0b0111_1111_1111),
    ],
)
def test_create_bitmask(bits, want):
    got = common._create_bitmask(bits)
    assert got == want


@pytest.mark.parametrize(
    "data, data_bits, send_end, want",
    [
        (b"\x01", None, False, b"\x01"),
        (b"hello world!", None, False, b"hello world!"),
        # Only apply the mask
        (b"\x03", 2, None, b"\x03"),  # 0b0000_0011 --> 0b0000_0011
        (b"\x04", 2, None, b"\x00"),  # 0b0000_0100 --> 0b0000_0000
        (b"\xff", 5, None, b"\x1f"),  # 0b1111_1111 --> 0b0001_1111
        (b"\xfe", 7, None, b"\x7e"),  # 0b1111_1110 --> 0b0111_1110
        (b"\xfe", 8, None, b"\xfe"),  # 0b1111_1110 --> 0b1111_1110
        (b"\xff", 9, None, b"\xff"),  # 0b1111_1111 --> 0b1111_1111
        # Always set highest bit *of data_bits* to 0
        (b"\x04", 2, False, b"\x00"),  # 0b0000_0100 --> 0b0000_0000
        (b"\x04", 3, False, b"\x00"),  # 0b0000_0100 --> 0b0000_0000
        (b"\x05", 3, False, b"\x01"),  # 0b0000_0101 --> 0b0000_0001
        (b"\xff", 7, False, b"\x3f"),  # 0b1111_1111 --> 0b0011_1111
        (b"\xff", 8, False, b"\x7f"),  # 0b1111_1111 --> 0b0111_1111
        # Always set highest bit *of data_bits* to 1
        (b"\x04", 2, True, b"\x02"),  # 0b0000_0100 --> 0b0000_0010
        (b"\x04", 3, True, b"\x04"),  # 0b0000_0100 --> 0b0000_0100
        (b"\x01", 3, True, b"\x05"),  # 0b0000_0001 --> 0b0000_0101
        (b"\x9f", 7, True, b"\x5f"),  # 0b1001_1111 --> 0b0101_1111
        (b"\x9f", 8, True, b"\x9f"),  # 0b1001_1111 --> 0b1001_1111
        # data_bits >8 bits act like data_bits=8, as type(data) is "bytes"
        # which is limited 8 bits per character.
        (b"\xff", 9, None, b"\xff"),
        (b"\xff", 9, False, b"\x7f"),
        (b"\xff", 9, True, b"\xff"),
        # send_end should only impact the final byte
        (b"\x6d\x5c\x25\x25", 4, None, b"\r\x0c\x05\x05"),
        (b"\x6d\x5c\x25\x25", 4, False, b"\r\x0c\x05\x05"),
        (b"\x6d\x5c\x25\x25", 4, True, b"\r\x0c\x05\x0d"),
        (b"`\xa0", 6, None, b"  "),
        (b"`\xa0", 6, False, b" \x00"),
        (b"`\xa0", 6, True, b"  "),
    ],
)
def test_iter_bytes(
    data: bytes, data_bits: Optional[int], send_end: bool, want: List[bytes]
) -> None:
    got = b"".join(common.iter_bytes(data, data_bits=data_bits, send_end=send_end))
    assert got == want


def test_iter_bytes_with_send_end_requires_data_bits() -> None:
    with pytest.raises(ValueError):
        # Need to wrap in list otherwise the iterator is never called.
        list(common.iter_bytes(b"", data_bits=None, send_end=True))


def test_iter_bytes_raises_on_bad_data_bits() -> None:
    with pytest.raises(ValueError):
        list(common.iter_bytes(b"", data_bits=0, send_end=None))
