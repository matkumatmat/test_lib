# tests/unit/test_cache.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from std_pack.infrastructure.cache.redis import RedisManager

@pytest.fixture
def mock_redis_client():
    """Mock objek Redis client asli."""
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.close.return_value = None
    mock.set.return_value = True
    mock.get.return_value = '{"id": 1, "name": "Kayez"}' # Return JSON string
    mock.delete.return_value = 1
    return mock

@pytest.mark.asyncio
async def test_redis_connection_init(mock_redis_client):
    """Test inisialisasi RedisManager."""
    # Patch aioredis.from_url agar mengembalikan mock kita
    with patch("redis.asyncio.from_url", return_value=mock_redis_client) as mock_from_url:
        manager = RedisManager("redis://localhost:6379/0")
        
        # 1. Init
        await manager.init_cache()
        
        # Assertions
        mock_from_url.assert_called_once()
        mock_redis_client.ping.assert_awaited_once()
        
        # 2. Get Client Access
        client = manager.get_client()
        assert client is mock_redis_client
        
        # 3. Close
        await manager.close()
        # Perbaiki: aclose() adalah method async di versi baru, close() sync
        # Tergantung versi redis-py, kita cek mana yang dipanggil code
        # Code Anda: await self.client.aclose()
        mock_redis_client.aclose.assert_awaited_once()

@pytest.mark.asyncio
async def test_redis_operations(mock_redis_client):
    """Test operasi via get_client()."""
    with patch("redis.asyncio.from_url", return_value=mock_redis_client):
        manager = RedisManager("redis://fake")
        await manager.init_cache()
        client = manager.get_client()

        # 1. Test SET
        await client.set("key", "val")
        mock_redis_client.set.assert_awaited_with("key", "val")

        # 2. Test GET
        val = await client.get("key")
        assert val == '{"id": 1, "name": "Kayez"}'