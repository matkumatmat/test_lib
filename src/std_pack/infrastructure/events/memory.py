"""
In-Memory Message Bus.
Cocok untuk testing atau komunikasi antar modul dalam satu service.
"""
from typing import Callable, Type
from collections import defaultdict

from std_pack.application.interfaces.ports import IMessageBus
from std_pack.domain import DomainEvent
from std_pack.infrastructure.logging import get_logger

logger = get_logger(__name__)

class MemoryMessageBus(IMessageBus):
    def __init__(self):
        self.subscribers: dict[Type[DomainEvent], list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable):
        """Mendaftarkan handler lokal."""
        self.subscribers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        event_type = type(event)
        handlers = self.subscribers.get(event_type, [])
        
        if handlers:
            logger.info("event_published_memory", name=event_type.__name__)
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error("event_handler_failed", error=str(e))

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)