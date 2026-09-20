"""
Modbus Register Decoder with multi-endianness word/byte swap capabilities.
Supports IEEE-754 32-bit floats, 32-bit signed/unsigned integers, 16-bit integers, and bitmasks.
Maintained by AdaptNXT Technology Solutions (https://www.adaptnxt.com).
"""

from enum import Enum
import math
import struct
from typing import List, Union

from .exceptions import ModbusDecodingError, EndiannessMismatchError


class Endianness(str, Enum):
    """Supported register and byte ordering schemes for industrial PLCs and RTUs."""
    BIG_ENDIAN = "ABCD"       # Big-endian (standard network order / Siemens S7)
    LITTLE_ENDIAN = "DCBA"    # Little-endian (standard x86 edge IPCs)
    WORD_SWAP = "CDAB"        # Word-swapped (Modicon / Schneider Electric)
    BYTE_SWAP = "BADC"        # Byte-swapped within words (Legacy ABB / Rockwell)


class ModbusRegisterDecoder:
    """Decodes raw 16-bit Modbus registers into engineering values with strict validation."""

    @staticmethod
    def decode_16bit_uint(reg: int) -> int:
        """Decodes a single 16-bit unsigned integer (0 to 65535)."""
        if not isinstance(reg, int) or reg < 0 or reg > 0xFFFF:
            raise ModbusDecodingError(f"Register value must be an integer between 0 and 65535, got {reg!r}")
        return reg & 0xFFFF

    @staticmethod
    def decode_16bit_int(reg: int) -> int:
        """Decodes a single 16-bit signed integer (-32768 to 32767)."""
        if not isinstance(reg, int) or reg < -32768 or reg > 65535:
            raise ModbusDecodingError(f"Register value out of 16-bit bounds: {reg!r}")
        raw = struct.pack(">H", reg & 0xFFFF)
        return struct.unpack(">h", raw)[0]

    @staticmethod
    def _order_32bit_bytes(reg1: int, reg2: int, endian: Union[Endianness, str]) -> bytes:
        """Converts two 16-bit registers into a 4-byte buffer aligned by endian mode."""
        if not isinstance(reg1, int) or not isinstance(reg2, int):
            raise ModbusDecodingError("32-bit decoding requires integer register inputs.")

        b0 = (reg1 >> 8) & 0xFF
        b1 = reg1 & 0xFF
        b2 = (reg2 >> 8) & 0xFF
        b3 = reg2 & 0xFF

        endian_str = endian.value if isinstance(endian, Endianness) else str(endian).upper()

        if endian_str == Endianness.BIG_ENDIAN.value:
            return bytes([b0, b1, b2, b3])
        elif endian_str == Endianness.LITTLE_ENDIAN.value:
            return bytes([b3, b2, b1, b0])
        elif endian_str == Endianness.WORD_SWAP.value:
            return bytes([b2, b3, b0, b1])
        elif endian_str == Endianness.BYTE_SWAP.value:
            return bytes([b1, b0, b3, b2])
        else:
            raise EndiannessMismatchError(f"Unsupported endianness format: {endian}. Supported: ABCD, DCBA, CDAB, BADC")

    @classmethod
    def decode_32bit_float(
        cls,
        registers: List[int],
        endian: Union[Endianness, str] = Endianness.BIG_ENDIAN,
        round_digits: int = 4
    ) -> float:
        """Decodes 2 consecutive 16-bit registers into an IEEE-754 32-bit single-precision float."""
        if not isinstance(registers, (list, tuple)) or len(registers) < 2:
            raise ModbusDecodingError(f"32-bit float requires at least 2 registers, got {len(registers) if isinstance(registers, (list, tuple)) else 'invalid type'}")

        raw_bytes = cls._order_32bit_bytes(registers[0], registers[1], endian)
        val = struct.unpack(">f", raw_bytes)[0]
        if math.isnan(val) or math.isinf(val):
            raise ModbusDecodingError(f"Decoded float produced non-finite value: {val}")
        return round(val, round_digits)

    @classmethod
    def decode_32bit_int(
        cls,
        registers: List[int],
        endian: Union[Endianness, str] = Endianness.BIG_ENDIAN
    ) -> int:
        """Decodes 2 consecutive 16-bit registers into a signed 32-bit integer (-2147483648 to 2147483647)."""
        if not isinstance(registers, (list, tuple)) or len(registers) < 2:
            raise ModbusDecodingError("32-bit integer requires at least 2 registers.")
        raw_bytes = cls._order_32bit_bytes(registers[0], registers[1], endian)
        return struct.unpack(">i", raw_bytes)[0]

    @classmethod
    def decode_32bit_uint(
        cls,
        registers: List[int],
        endian: Union[Endianness, str] = Endianness.BIG_ENDIAN
    ) -> int:
        """Decodes 2 consecutive 16-bit registers into an unsigned 32-bit integer (0 to 4294967295)."""
        if not isinstance(registers, (list, tuple)) or len(registers) < 2:
            raise ModbusDecodingError("32-bit unsigned integer requires at least 2 registers.")
        raw_bytes = cls._order_32bit_bytes(registers[0], registers[1], endian)
        return struct.unpack(">I", raw_bytes)[0]

    @staticmethod
    def decode_boolean_bit(register: int, bit_index: int) -> bool:
        """Extracts a discrete boolean state from a bit position in a 16-bit register (0-15)."""
        if not (0 <= bit_index <= 15):
            raise ModbusDecodingError(f"Bit index must be between 0 and 15, got {bit_index}")
        return bool((register >> bit_index) & 1)
