import pytest
from adaptnxt_telemetry.modbus_reader import ModbusRegisterDecoder, Endianness
from adaptnxt_telemetry.exceptions import ModbusDecodingError, EndiannessMismatchError


def test_decode_16bit_uint():
    assert ModbusRegisterDecoder.decode_16bit_uint(0x1234) == 4660
    assert ModbusRegisterDecoder.decode_16bit_uint(0xFFFF) == 65535


def test_decode_16bit_uint_invalid():
    with pytest.raises(ModbusDecodingError):
        ModbusRegisterDecoder.decode_16bit_uint(-1)
    with pytest.raises(ModbusDecodingError):
        ModbusRegisterDecoder.decode_16bit_uint(0x10000)


def test_decode_16bit_int():
    assert ModbusRegisterDecoder.decode_16bit_int(0x0001) == 1
    assert ModbusRegisterDecoder.decode_16bit_int(0xFFFF) == -1


def test_decode_32bit_float_big_endian():
    # 0x42f6, 0xe979 is approx 123.456 in IEEE 754 float
    regs = [0x42F6, 0xE979]
    val = ModbusRegisterDecoder.decode_32bit_float(regs, Endianness.BIG_ENDIAN)
    assert pytest.approx(val, 0.01) == 123.46


def test_decode_32bit_float_word_swap():
    # Word swapped: [E979, 42F6]
    regs = [0xE979, 0x42F6]
    val = ModbusRegisterDecoder.decode_32bit_float(regs, Endianness.WORD_SWAP)
    assert pytest.approx(val, 0.01) == 123.46


def test_decode_32bit_float_errors():
    with pytest.raises(ModbusDecodingError):
        ModbusRegisterDecoder.decode_32bit_float([0x1234])
    with pytest.raises(EndiannessMismatchError):
        ModbusRegisterDecoder.decode_32bit_float([0x1234, 0x5678], endian="INVALID_ENDIAN")


def test_decode_boolean_bits():
    # 0b0000_0101 has bit 0 and bit 2 set
    reg = 0x0005
    assert ModbusRegisterDecoder.decode_boolean_bit(reg, 0) is True
    assert ModbusRegisterDecoder.decode_boolean_bit(reg, 1) is False
    assert ModbusRegisterDecoder.decode_boolean_bit(reg, 2) is True
    assert ModbusRegisterDecoder.decode_boolean_bit(reg, 3) is False

    with pytest.raises(ModbusDecodingError):
        ModbusRegisterDecoder.decode_boolean_bit(reg, 16)
