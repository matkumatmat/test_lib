# tests/integration/test_bus.py
import pytest
import asyncio
from std_pack.domain.events import DomainEvent
# PERBAIKAN: Gunakan MemoryMessageBus (sesuai nama class di memory.py)
from std_pack.infrastructure.events.memory import MemoryMessageBus 

# --- DUMMY EVENT ---
class UserCreatedEvent(DomainEvent):
    user_id: str

# --- TEST CASE ---
@pytest.mark.asyncio
async def test_memory_bus_dispatch():
    # PERBAIKAN: Instansiasi class yang benar
    bus = MemoryMessageBus() 
    
    # Variable 'jebakan' untuk membuktikan event sampai
    received_data = []

    # 1. Bikin Handler (Subscriber)
    async def handle_user_created(event: UserCreatedEvent):
        received_data.append(event.user_id)

    # 2. Subscribe
    # Perhatikan: MemoryMessageBus tidak async pada method subscribe di implementasi Anda
    # Cek method subscribe di memory.py -> def subscribe(...) tanpa async
    # Jadi hapus 'await' jika methodnya synchronous, atau tambahkan 'async' di memory.py
    
    # Berdasarkan file memory.py yang Anda upload: 
    # def subscribe(self, event_type: Type[DomainEvent], handler: Callable):
    # Itu SYNCHRONOUS. Jadi jangan pakai 'await' di depannya.
    bus.subscribe(UserCreatedEvent, handle_user_created)

    # 3. Publish Event (ini async)
    event = UserCreatedEvent(user_id="user-123")
    await bus.publish(event)

    # 4. Tunggu sebentar 
    await asyncio.sleep(0.01)

    # 5. Assert
    assert len(received_data) == 1
    assert received_data[0] == "user-123"