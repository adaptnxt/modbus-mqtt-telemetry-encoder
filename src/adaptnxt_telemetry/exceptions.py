"""
Custom exceptions for the AdaptNXT Telemetry & Edge Buffer suite.
Maintained by AdaptNXT Technology Solutions (https://www.adaptnxt.com).
"""


class TelemetryError(Exception):
    """Base exception for all AdaptNXT telemetry operations."""
    pass


class ModbusDecodingError(TelemetryError):
    """Raised when raw register decoding fails due to invalid data length, corruption, or unsupported formats."""
    pass


class EndiannessMismatchError(ModbusDecodingError):
    """Raised when an invalid byte/word order permutation is supplied."""
    pass


class BufferError(TelemetryError):
    """Base exception for local storage and queue buffer failures."""
    pass


class BufferCapacityExceededError(BufferError):
    """Raised when the persistent buffer exceeds configured max storage capacity."""
    pass


class MqttPublishError(TelemetryError):
    """Raised when message publication to MQTT broker fails repeatedly."""
    pass
