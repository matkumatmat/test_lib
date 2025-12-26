"""
Redis Message Bus.
Untuk komunikasi antar Microservices (Event Driven).
"""
import json
from std_pack.application.interfaces.ports import IMessageBus
from std_pack.domain import DomainEvent
from std_pack.infrastructure.cache import RedisManager
from std_pack.infrastructure.logging import get_logger

logger = get_logger(__name__)

class RedisMessageBus(IMessageBus):
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager

    async def publish(self, event: DomainEvent) -> None:
        client = self.redis.get_client()
        
        # Channel name convention: events:{event_name}
        channel = f"events:{event.event_type}"
        
        # Serialize Event ke JSON
        # Asumsi DomainEvent adalah Pydantic Model
        payload = event.model_dump_json()
        
        await client.publish(channel, payload)
        logger.info("event_published_redis", channel=channel, id=str(event.event_id))

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        # Menggunakan Pipeline untuk performa
        client = self.redis.get_client()
        async with client.pipeline() as pipe:
            for event in events:
                channel = f"events:{event.event_type}"
                payload = event.model_dump_json()
                pipe.publish(channel, payload)
            
            await pipe.execute()
            logger.info("event_batch_published_redis", count=len(events))