import os
import tempfile
import pytest
from adaptnxt_telemetry.buffer_manager import SQLiteStoreAndForwardBuffer


@pytest.fixture
def temp_buffer():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    buf = SQLiteStoreAndForwardBuffer(db_path=db_path)
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
