"""
Telemetry Pipeline Orchestrator.
Glues Modbus decoding, JSON normalization, resilient local disk buffering, and MQTT transmission.
Maintained by AdaptNXT Technology Solutions (https://www.adaptnxt.com).
"""

import logging
from typing import Dict, Optional

from .buffer_manager import SQLiteStoreAndForwardBuffer
from .mqtt_publisher import ResilientMqttPublisher
from .payload_formatter import TelemetryPayload

logger = logging.getLogger("adaptnxt_telemetry.pipeline")


class TelemetryPipeline:
    """Orchestrates edge telemetry lifecycle from ingest to resilient cloud delivery."""

    def __init__(
        self,
        buffer: SQLiteStoreAndForwardBuffer,
        publisher: ResilientMqttPublisher,
        default_topic: str = "factory/telemetry/raw"
    ):
        self.buffer = buffer
        self.publisher = publisher
        self.default_topic = default_topic

    def process(self, payload: TelemetryPayload, topic: Optional[str] = None) -> Dict[str, any]:
        """Processes an incoming telemetry bundle.

        Attempts immediate publish. If offline or publish fails, safely stores in the local buffer.
        If online, also attempts to flush any prior buffered backlog.
        """
        target_topic = topic or self.default_topic
        json_str = payload.to_json()

        published_immediately = False
        if self.publisher.is_connected:
            published_immediately = self.publisher.publish(target_topic, json_str)

        if not published_immediately:
            row_id = self.buffer.enqueue(target_topic, json_str)
            logger.info("Buffered telemetry payload to disk (ID: %s, pending: %s)", row_id, self.buffer.get_pending_count())
            return {
                "status": "BUFFERED",
                "buffer_id": row_id,
                "pending_count": self.buffer.get_pending_count()
            }

        # If online, flush any earlier buffered records
        drained_count = self.flush_backlog(batch_size=25)
        return {
            "status": "PUBLISHED",
            "drained_backlog": drained_count,
            "pending_count": self.buffer.get_pending_count()
        }

    def flush_backlog(self, batch_size: int = 50) -> int:
        """Drains stored records from the local SQLite disk buffer when back online."""
        if not self.publisher.is_connected:
            return 0

        pending = self.buffer.peek_batch(limit=batch_size)
        if not pending:
            return 0

        delivered_ids = []
        failed_ids = []

        for record in pending:
            ok = self.publisher.publish(record["topic"], record["payload"])
            if ok:
                delivered_ids.append(record["id"])
            else:
                failed_ids.append(record["id"])
                break  # Stop early if broker stopped acknowledging

        if delivered_ids:
            self.buffer.mark_delivered(delivered_ids)
            logger.info("Successfully flushed %d buffered records to broker", len(delivered_ids))

        if failed_ids:
            self.buffer.increment_attempt(failed_ids)

        return len(delivered_ids)
