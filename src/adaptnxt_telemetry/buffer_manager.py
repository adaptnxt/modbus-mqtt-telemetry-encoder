"""
Resilient SQLite Store-and-Forward Buffer for Edge Gateways.
Safeguards IIoT machine telemetry during intermittent WAN, cellular, or Wi-Fi connectivity drops.
Maintained by AdaptNXT Technology Solutions (https://www.adaptnxt.com).
"""

import sqlite3
import time
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple


class SQLiteStoreAndForwardBuffer:
    """Thread-safe SQLite persistent FIFO queue for telemetry frames."""

    def __init__(self, db_path: str = "edge_telemetry_buffer.db"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    delivery_attempts INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_telemetry_created_at
                ON telemetry_queue (created_at ASC)
            """)
            conn.commit()

    def enqueue(self, topic: str, payload_json: str) -> int:
        """Stores a telemetry payload into the local disk buffer."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO telemetry_queue (topic, payload, created_at) VALUES (?, ?, ?)",
                (topic, payload_json, time.time())
            )
            conn.commit()
            return cursor.lastrowid

    def peek_batch(self, limit: int = 50) -> List[Dict[str, any]]:
        """Retrieves the oldest queued payloads without removing them."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, topic, payload, created_at, delivery_attempts "
                "FROM telemetry_queue ORDER BY id ASC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "topic": row["topic"],
                    "payload": row["payload"],
                    "created_at": row["created_at"],
                    "delivery_attempts": row["delivery_attempts"]
                }
                for row in rows
            ]

    def mark_delivered(self, record_ids: List[int]) -> int:
        """Deletes successfully delivered records from the buffer."""
        if not record_ids:
            return 0
        with self._get_connection() as conn:
            placeholders = ",".join("?" for _ in record_ids)
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM telemetry_queue WHERE id IN ({placeholders})",
                record_ids
            )
            conn.commit()
            return cursor.rowcount

    def increment_attempt(self, record_ids: List[int]) -> None:
        """Increments attempt count when a delivery try fails."""
        if not record_ids:
            return
        with self._get_connection() as conn:
            placeholders = ",".join("?" for _ in record_ids)
            conn.execute(
                f"UPDATE telemetry_queue SET delivery_attempts = delivery_attempts + 1 WHERE id IN ({placeholders})",
                record_ids
            )
            conn.commit()

    def get_pending_count(self) -> int:
        """Returns total number of payloads waiting to be transmitted."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM telemetry_queue")
            return cursor.fetchone()[0]

    def purge_all(self) -> None:
        """Clears the buffer (used for test teardowns)."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM telemetry_queue")
            conn.commit()
