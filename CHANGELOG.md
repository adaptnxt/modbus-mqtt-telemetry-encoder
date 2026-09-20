# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-20

### Added
- Modbus multi-endianness register decoding (`ModbusRegisterDecoder`) for 32-bit floats, 32-bit integers, 16-bit integers, and bitmasks.
- Support for Big-Endian (`ABCD`), Little-Endian (`DCBA`), Word-Swapped (`CDAB`), and Byte-Swapped (`BADC`) register permutations.
- Persistent SQLite store-and-forward queue (`SQLiteStoreAndForwardBuffer`) with WAL mode, FIFO ordering, and max storage capacity limits.
- Resilient MQTT publisher wrapper (`ResilientMqttPublisher`) with auto-reconnection and mock simulation mode.
- Standardized IIoT JSON telemetry batch formatter (`TelemetryPayload`, `TelemetryPoint`).
- Command-line interface (`adaptnxt-telemetry`) for inspecting queue state and running machine simulations.
- End-to-end CNC machine failure simulation script (`examples/simulated_factory_machine.py`).
- Automated pytest test suite covering unit decoders, buffer transactions, and telemetry serializations.
- GitHub Actions CI workflow supporting Python 3.10 through 3.14.
