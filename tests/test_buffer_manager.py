import os
import tempfile
import pytest
from adaptnxt_telemetry.buffer_manager import SQLiteStoreAndForwardBuffer
from adaptnxt_telemetry.exceptions import BufferCapacityExceededError


@pytest.fixture
def temp_buffer():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    buf = SQLiteStoreAndForwardBuffer(db_path=db_path, max_records=10)
    yield buf
    buf.purge_all()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_enqueue_and_peek(temp_buffer):
    assert temp_buffer.get_pending_count() == 0

    temp_buffer.enqueue("factory/temp", '{"value": 42}')
    temp_buffer.enqueue("factory/press", '{"value": 100}')

    assert temp_buffer.get_pending_count() == 2

    batch = temp_buffer.peek_batch(limit=10)
    assert len(batch) == 2
    assert batch[0]["topic"] == "factory/temp"
    assert batch[1]["topic"] == "factory/press"


def test_mark_delivered(temp_buffer):
    id1 = temp_buffer.enqueue("topic/1", '{"v": 1}')
    id2 = temp_buffer.enqueue("topic/2", '{"v": 2}')
    id3 = temp_buffer.enqueue("topic/3", '{"v": 3}')

    assert temp_buffer.get_pending_count() == 3

    # Delete first 2
    deleted = temp_buffer.mark_delivered([id1, id2])
    assert deleted == 2
    assert temp_buffer.get_pending_count() == 1

    remaining = temp_buffer.peek_batch(limit=10)
    assert remaining[0]["id"] == id3


def test_capacity_drop_oldest():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    buf = SQLiteStoreAndForwardBuffer(db_path=db_path, max_records=5, drop_oldest_on_full=True)
    try:
        for i in range(7):
            buf.enqueue(f"topic/{i}", f'{{"i": {i}}}')

        # When 6th item was added, max was 5, so 1 item (5% or min 1) dropped
        # Pending count stays bounded
        assert buf.get_pending_count() <= 6
    finally:
        buf.purge_all()
        if os.path.exists(db_path):
            os.remove(db_path)


def test_capacity_strict_raise():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    buf = SQLiteStoreAndForwardBuffer(db_path=db_path, max_records=3, drop_oldest_on_full=False)
    try:
        buf.enqueue("topic/1", "{}")
        buf.enqueue("topic/2", "{}")
        buf.enqueue("topic/3", "{}")
        with pytest.raises(BufferCapacityExceededError):
            buf.enqueue("topic/4", "{}")
    finally:
        buf.purge_all()
        if os.path.exists(db_path):
            os.remove(db_path)
