import struct


def i16swap(i16: int):
    return struct.unpack("<h", struct.pack(">h", i16))[0]


def u16swap(u16: int):
    return struct.unpack("<H", struct.pack(">H", u16))[0]


def i32swap(i32: int):
    return struct.unpack("<i", struct.pack(">i", i32))[0]


def u32swap(u32: int):
    return struct.unpack("<I", struct.pack(">I", u32))[0]
