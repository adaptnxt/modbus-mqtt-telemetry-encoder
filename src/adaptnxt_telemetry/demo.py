"""
End-to-End Demonstration: Modbus Register Simulation with Resilient Store-and-Forward Buffer.
Shows edge offline resilience when an MQTT broker experiences an outage.
Maintained by AdaptNXT Technology Solutions (https://www.adaptnxt.com).
"""

import sys
import os
import time
import tempfile

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
    print(" [REFERENCE DEMONSTRATION]")
    print("================================================================\n")

    db_dir = tempfile.gettempdir()
    db_file = os.path.join(db_dir, "adaptnxt_demo_buffer.db")
    buffer = SQLiteStoreAndForwardBuffer(db_path=db_file)
    buffer.purge_all()

    # Step 1: Initialize publisher in mock mode for demonstration
    publisher = ResilientMqttPublisher(mock_mode=True)
    publisher.connect()
    pipeline = TelemetryPipeline(buffer=buffer, publisher=publisher, default_topic="factory/line-1/press-04")

    # Step 2: Simulate reading Modbus registers from a CNC / Press machine
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
        TelemetryPoint("is_running", is_running, raw_register=103),
        TelemetryPoint("alarm_active", has_alarm, raw_register=103)
    ]

    # Step 3: Publish directly while connected
    print("[Publishing Real-Time Payload via Live MQTT Connection]")
    payload = format_telemetry_batch("press-04-cell", points)
    pipeline.ingest("factory/line-1/press-04", payload)
    print(" -> Packet dispatched to MQTT broker without buffering.\n")

    # Step 4: Simulate Network Outage
    print("[Simulating Factory Network Disconnection / Broker Outage]")
    publisher.is_connected = False
    print(" -> MQTT Broker offline. Ingesting subsequent machine cycles...")

    for cycle in range(1, 4):
        p = format_telemetry_batch("press-04-cell", [
            TelemetryPoint("cycle_index", cycle),
            TelemetryPoint("temperature_c", 65.2 + cycle * 1.5, unit="celsius")
        ])
        pipeline.ingest("factory/line-1/press-04", p)

    print(f" -> Safely queued into SQLite Store-and-Forward Buffer: {buffer.get_pending_count()} packets\n")

    # Step 5: Network Restored
    print("[Factory Network Restored / Broker Reconnected]")
    publisher.is_connected = True
    drained = pipeline.drain_backlog()
    print(f" -> Backlog flushed to MQTT broker: {drained} queued messages.")
    print(f" -> Final Pending Buffer Count:    {buffer.get_pending_count()} messages.")

    print("\n================================================================")
    print(" Demonstration Finished Successfully.")
    print("================================================================")


if __name__ == "__main__":
    run_demo()
