import json
from adaptnxt_telemetry.payload_formatter import TelemetryPoint, format_telemetry_batch


def test_payload_formatting():
    points = [
        TelemetryPoint("temperature", 78.4, unit="C"),
        TelemetryPoint("rpm", 1500, unit="rpm")
    ]

    payload = format_telemetry_batch(
        device_id="motor-01",
        site_id="plant-a",
        points=points,
        edge_id="gw-01"
    )

    data = payload.to_dict()
    assert data["device_id"] == "motor-01"
    assert data["site_id"] == "plant-a"
    assert data["metrics"]["temperature"] == 78.4
    assert data["metrics"]["rpm"] == 1500
    assert len(data["metrics_detail"]) == 2

    # Verify valid JSON serialization
    json_str = payload.to_json()
    loaded = json.loads(json_str)
    assert loaded["device_id"] == "motor-01"
