"""
Standardized IIoT Telemetry Formatter.
Serializes machine telemetry points into cloud-ready JSON schemas compatible with AWS IoT, Azure IoT Hub, and ThingsBoard.
Maintained by AdaptNXT Technology Solutions (https://www.adaptnxt.com).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json


class TelemetryPoint:
    """Represents a single sensor reading or machine telemetry metric."""

    def __init__(
        self,
        name: str,
        value: Any,
        unit: str = "",
        quality: str = "GOOD",
        raw_register: Optional[int] = None
    ):
        self.name = name
        self.value = value
        self.unit = unit
        self.quality = quality
        self.raw_register = raw_register

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "quality": self.quality,
        }
        if self.raw_register is not None:
            data["raw_register"] = self.raw_register
        return data


class TelemetryPayload:
    """Complete machine telemetry message bundle with edge gateway metadata."""

    def __init__(
        self,
        device_id: str,
        site_id: str,
        metrics: List[TelemetryPoint],
        timestamp: Optional[datetime] = None,
        edge_id: str = "adaptnxt-edge-gw"
    ):
        self.device_id = device_id
        self.site_id = site_id
        self.metrics = metrics
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.edge_id = edge_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "site_id": self.site_id,
            "edge_id": self.edge_id,
            "timestamp": self.timestamp.isoformat(),
            "metrics": {m.name: m.value for m in self.metrics},
            "metrics_detail": [m.to_dict() for m in self.metrics]
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def format_telemetry_batch(
    device_id: str,
    site_id: str,
    points: List[TelemetryPoint],
    edge_id: str = "adaptnxt-edge-gw"
) -> TelemetryPayload:
    """Convenience helper to bundle points into a TelemetryPayload."""
    return TelemetryPayload(
        device_id=device_id,
        site_id=site_id,
        metrics=points,
        edge_id=edge_id
    )
