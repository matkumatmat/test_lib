"""
Application Ports / Interfaces.
Berisi kontrak untuk alat-alat orkestrasi (Transaction & Messaging).
Lokasi: src/std_pack/application/interfaces/ports.py
"""
from typing import Protocol, runtime_checkable
try:
    from std_pack.domain import DomainEvent
except ImportError: # pragma: no cover
    from ...domain import DomainEvent # pragma: no cover

# --- UNIT OF WORK (Transaction Management) ---
@runtime_checkable
class IUnitOfWork(Protocol):
    """
    Port: Mengelola transaksi atomik (Command Pattern support).
    Digunakan oleh Service untuk menjamin data konsisten.
    """
    async def __aenter__(self) -> "IUnitOfWork": ...
    async def __aexit__(self, exc_type, exc_value, traceback) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...

# --- MESSAGE BUS (Observer Pattern) ---
class IMessageBus(Protocol):
    """
    Port: Mengirim event ke dunia luar (Observer Pattern).
    Digunakan oleh Service untuk publikasi event.
    """
    async def publish(self, event: DomainEvent) -> None:
        """Publish satu event."""
        ...
        
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish banyak event sekaligus."""
        ...