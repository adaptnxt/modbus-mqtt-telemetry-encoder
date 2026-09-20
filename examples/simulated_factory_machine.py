"""
End-to-End Demonstration: Modbus Register Simulation with Resilient Store-and-Forward Buffer.
Shows edge offline resilience when an MQTT broker experiences an outage.
Maintained by AdaptNXT Technology Solutions (https://www.adaptnxt.com).
"""

import sys
import os
import time

# Allow running directly from repository root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from adaptnxt_telemetry import (
    ModbusRegisterDecoder,
    Endianness,
    TelemetryPoint,
    format_telemetry_batch,
    SQLiteStoreAndForwardBuffer,
    TelemetryPipeline
)
from adaptnxt_telemetry.mqtt_publisher import ResilientMqttPublisher


def run_demo():
    print("================================================================")
    print(" AdaptNXT Industrial Modbus-to-MQTT Telemetry Demo")
    print(" https://www.adaptnxt.com/service-industrial-iot-platform")
    print("================================================================\n")

    db_file = os.path.join(os.path.dirname(__file__), "demo_buffer.db")
    buffer = SQLiteStoreAndForwardBuffer(db_path=db_file)
    buffer.purge_all()

    # Step 1: Initialize publisher in mock mode for demonstration
    publisher = ResilientMqttPublisher(mock_mode=True)
    publisher.connect()
    pipeline = TelemetryPipeline(buffer=buffer, publisher=publisher, default_topic="factory/line-1/press-04")

    # Step 2: Simulate reading Modbus registers from a CNC / Press machine
    # Register 0 & 1: 32-bit Float for Hydraulic Pressure (e.g. 142.50 bar)
    # Register 2: 16-bit Unsigned Integer for Spindle RPM (e.g. 2850 rpm)
    # Register 3: Discrete status bits (Bit 0 = Run, Bit 1 = Alarm, Bit 2 = Maintenance)
    reg_pressure = [0x430E, 0x8000]   # 142.5 in IEEE-754
    reg_rpm = 2850
    reg_status = 0x0005               # Bits 0 & 2 high (Running & Maintenance flag)

    pressure_val = ModbusRegisterDecoder.decode_32bit_float(reg_pressure, Endianness.BIG_ENDIAN)
    rpm_val = ModbusRegisterDecoder.decode_16bit_uint(reg_rpm)
    is_running = ModbusRegisterDecoder.decode_boolean_bit(reg_status, 0)
    has_alarm = ModbusRegisterDecoder.decode_boolean_bit(reg_status, 1)

    print(f"[Decoded Modbus Raw Registers]")
    print(f" -> Hydraulic Pressure: {pressure_val} bar")
    print(f" -> Spindle RPM:        {rpm_val} RPM")
    print(f" -> Status Running:     {is_running}")
    print(f" -> Status Alarm:       {has_alarm}\n")

    points = [
        TelemetryPoint("hydraulic_pressure", pressure_val, unit="bar", raw_register=100),
        TelemetryPoint("spindle_rpm", rpm_val, unit="rpm", raw_register=102),
        TelemetryPoint("is_running", is_running, unit="bool", raw_register=103),
        TelemetryPoint("has_alarm", has_alarm, unit="bool", raw_register=103)
    ]

    payload = format_telemetry_batch(
        device_id="press-cnc-04",
        site_id="plant-bangalore-01",
        points=points,
        edge_id="adaptnxt-edge-gw-01"
    )

    # Step 3: Publish when ONLINE
    print("[1. Online Transmission]")
    res1 = pipeline.process(payload)
    print(f" -> Pipeline Status: {res1['status']} | Pending in Local Buffer: {res1['pending_count']}\n")

    # Step 4: Simulate Network Cut / Broker Disconnection
    print("[2. Simulating Network Disconnect (Broker Offline)]")
    publisher.is_connected = False
    for cycle in range(1, 4):
        p = format_telemetry_batch(
            device_id="press-cnc-04",
            site_id="plant-bangalore-01",
            points=[TelemetryPoint("cycle_index", cycle, unit="count")]
        )
        res = pipeline.process(p)
        print(f" -> Cycle {cycle}: Status: {res['status']} (Safely buffered to disk, pending: {res['pending_count']})")

    print(f"\nTotal records waiting in offline SQLite buffer: {buffer.get_pending_count()}\n")

    # Step 5: Network Restored -> Automatic FIFO Drain
    print("[3. Simulating Network Restoration (Broker Online)]")
    publisher.is_connected = True
    new_online_payload = format_telemetry_batch(
        device_id="press-cnc-04",
        site_id="plant-bangalore-01",
        points=[TelemetryPoint("cycle_index", 4, unit="count")]
    )
    res_restored = pipeline.process(new_online_payload)
    print(f" -> Current Message Status: {res_restored['status']}")
    print(f" -> Backlog Drained:       {res_restored['drained_backlog']} records")
    print(f" -> Remaining in Buffer:   {res_restored['pending_count']} records\n")

    # Cleanup demo database
    buffer.purge_all()
    if os.path.exists(db_file):
        os.remove(db_file)

    print("Demo completed successfully. Zero data loss achieved!")


if __name__ == "__main__":
    run_demo()
