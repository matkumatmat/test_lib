import pytest
from unittest.mock import AsyncMock, MagicMock
from std_pack.infrastructure.events.redis_bus import RedisMessageBus
from std_pack.domain.events import DomainEvent

class DummyEvent(DomainEvent):
    data: str

@pytest.mark.asyncio
async def test_redis_bus_publish():
    # --- SETUP MOCK YANG PRESISI ---
    mock_manager = MagicMock()
    mock_client = AsyncMock()
    mock_manager.get_client.return_value = mock_client

    # 1. Setup Pipeline Object
    # Pipeline itu sendiri support 'async with', jadi dia AsyncMock
    mock_pipeline_obj = AsyncMock()
    mock_pipeline_obj.__aenter__.return_value = mock_pipeline_obj
    mock_pipeline_obj.__aexit__.return_value = None
    
    # KUNCI PERBAIKAN: Method 'publish' di pipeline itu SYNC (antrian)
    # Kita paksa jadi MagicMock agar tidak return coroutine
    mock_pipeline_obj.publish = MagicMock()
    
    # Method 'execute' di pipeline itu ASYNC
    mock_pipeline_obj.execute = AsyncMock()

    # 2. Setup client.pipeline()
    # client.pipeline() itu function SYNC yang return object pipeline
    mock_client.pipeline = MagicMock(return_value=mock_pipeline_obj)

    # --- EXECUTE TEST ---
    bus = RedisMessageBus(redis_manager=mock_manager)
    event = DummyEvent(data="test")

    # A. Test Publish Single (Non-Pipeline)
    await bus.publish(event)
    mock_client.publish.assert_awaited_once()

    # B. Test Publish Batch (Pipeline)
    events = [DummyEvent(data="A"), DummyEvent(data="B")]
    await bus.publish_batch(events)
    
    # Verifikasi
    mock_client.pipeline.assert_called_once() # Sync call
    assert mock_pipeline_obj.publish.call_count == 2 # Sync call (tidak perlu await)
    mock_pipeline_obj.execute.assert_awaited_once() # Async call