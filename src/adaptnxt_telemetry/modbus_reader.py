"""
Modbus Register Decoder with multi-endianness word/byte swap capabilities.
Supports IEEE-754 32-bit floats, 32-bit integers, 16-bit integers, and bitmasks.
Maintained by AdaptNXT Technology Solutions (https://www.adaptnxt.com).
"""

from enum import Enum
import struct
from typing import List, Union


class Endianness(str, Enum):
    BIG_ENDIAN = "ABCD"       # Big-endian (standard network order)
    LITTLE_ENDIAN = "DCBA"    # Little-endian
    WORD_SWAP = "CDAB"        # Word-swapped (common in Modicon / Schneider PLCs)
    BYTE_SWAP = "BADC"        # Byte-swapped within words


class ModbusRegisterDecoder:
    """Decodes raw 16-bit Modbus registers into engineering values."""

    @staticmethod
    def decode_16bit_uint(reg: int) -> int:
        return reg & 0xFFFF

    @staticmethod
    def decode_16bit_int(reg: int) -> int:
        raw = struct.pack(">H", reg & 0xFFFF)
        return struct.unpack(">h", raw)[0]

    @staticmethod
    def _order_32bit_bytes(reg1: int, reg2: int, endian: Endianness) -> bytes:
        """Converts two 16-bit registers into a 4-byte buffer aligned by endian mode."""
        b0 = (reg1 >> 8) & 0xFF
        b1 = reg1 & 0xFF
        b2 = (reg2 >> 8) & 0xFF
        b3 = reg2 & 0xFF

        if endian == Endianness.BIG_ENDIAN:
            return bytes([b0, b1, b2, b3])
        elif endian == Endianness.LITTLE_ENDIAN:
            return bytes([b3, b2, b1, b0])
        elif endian == Endianness.WORD_SWAP:
            return bytes([b2, b3, b0, b1])
        elif endian == Endianness.BYTE_SWAP:
            return bytes([b1, b0, b3, b2])
        else:
            raise ValueError(f"Unsupported endianness format: {endian}")

    @classmethod
    def decode_32bit_float(cls, registers: List[int], endian: Endianness = Endianness.BIG_ENDIAN) -> float:
        """Decodes 2 consecutive 16-bit registers into an IEEE-754 32-bit float."""
        if len(registers) < 2:
            raise ValueError("Decoding 32-bit float requires at least 2 consecutive 16-bit registers.")
        raw_bytes = cls._order_32bit_bytes(registers[0], registers[1], endian)
        return round(struct.unpack(">f", raw_bytes)[0], 4)

    @classmethod
    def decode_32bit_int(cls, registers: List[int], endian: Endianness = Endianness.BIG_ENDIAN) -> int:
        """Decodes 2 consecutive 16-bit registers into a signed 32-bit integer."""
        if len(registers) < 2:
            raise ValueError("Decoding 32-bit integer requires at least 2 consecutive 16-bit registers.")
        raw_bytes = cls._order_32bit_bytes(registers[0], registers[1], endian)
        return struct.unpack(">i", raw_bytes)[0]

    @classmethod
    def decode_32bit_uint(cls, registers: List[int], endian: Endianness = Endianness.BIG_ENDIAN) -> int:
        """Decodes 2 consecutive 16-bit registers into an unsigned 32-bit integer."""
        if len(registers) < 2:
            raise ValueError("Decoding 32-bit unsigned integer requires at least 2 consecutive 16-bit registers.")
        raw_bytes = cls._order_32bit_bytes(registers[0], registers[1], endian)
        return struct.unpack(">I", raw_bytes)[0]

    @staticmethod
    def decode_boolean_bit(register: int, bit_index: int) -> bool:
        """Extracts a discrete boolean state from a bit position in a 16-bit register (0-15)."""
        if not (0 <= bit_index <= 15):
            raise ValueError("Bit index must be between 0 and 15.")
        return bool((register >> bit_index) & 1)
