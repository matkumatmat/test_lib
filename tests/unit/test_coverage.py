# tests/unit/test_final_sweep.py

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.orm import Mapped, mapped_column

# Import Components
from std_pack.infrastructure.security.rbac import PermissionDependency
from std_pack.infrastructure.security.token import TokenHelper
from std_pack.infrastructure.cache.redis import RedisManager
from std_pack.domain.exceptions import ForbiddenError, UnauthorizedError
from std_pack.infrastructure.persistence.repositories import SqlAlchemyRepository
from std_pack.infrastructure.persistence.models import BaseDBModel
from std_pack.domain.entities import BaseEntity
from std_pack.infrastructure.security.scheme import get_current_token_payload, get_current_user

# --- SETUP DUMMY MODEL (Perbaikan Utama) ---
# Kita butuh Entity dan Model yang SEJAJAR untuk test repository
class SweeperEntity(BaseEntity):
    name: str

class SweeperModel(BaseDBModel):
    __tablename__ = "sweepers"
    # BaseDBModel sudah punya id, created_at, updated_at
    name: Mapped[str]

# --- 1. FIX RBAC (Forbidden Logic - 78% -> 100%) ---
@pytest.mark.asyncio
async def test_rbac_forbidden_scenario():
    """Simulasi: User Login, tapi Role tidak cukup."""
    dependency = PermissionDependency(required_permission="super_admin")
    
    mock_user = MagicMock()
    mock_user.is_active = True
    mock_user.roles = ["guest"] # Role tidak cocok
    # Hapus method has_permission agar library cek manual ke list roles
    del mock_user.has_permission 

    with pytest.raises(ForbiddenError):
        await dependency(mock_user)

# --- 2. FIX TOKEN (Default Expiry - 91% -> 100%) ---
def test_token_default_expiry():
    """Simulasi: Bikin token tanpa menentukan waktu expired."""
    mock_settings = MagicMock()
    mock_settings.SECRET_KEY = "secret"
    mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
    
    helper = TokenHelper(mock_settings)
    
    # Panggil TANPA parameter expires_delta
    token = helper.create_access_token("user_1")
    payload = helper.decode_token(token)
    assert "exp" in payload

# --- 3. FIX REDIS (Close Safety - 83% -> 100%) ---
@pytest.mark.asyncio
async def test_redis_close_disconnected():
    """Simulasi: Menutup koneksi yang belum pernah dibuka."""
    manager = RedisManager("redis://fake")
    # Langsung close. Harusnya tidak error walau client masih None
    await manager.close()
    
    # Kita tidak cek properti is_connected karena internal implementation
    # Cukup pastikan tidak crash
    assert manager.client is None

# --- 4. FIX REPOSITORY (Edge Cases - 100%) ---
@pytest.mark.asyncio
async def test_repo_edge_cases():
    """Simulasi: Save kosong dan Delete hantu."""
    mock_session = AsyncMock()
    
    # GUNAKAN MODEL YANG KITA DEFINISIKAN DI ATAS
    repo = SqlAlchemyRepository(mock_session, SweeperEntity, SweeperModel)
    
    # Case A: Save List Kosong
    result = await repo.save_all([])
    assert result == []
    mock_session.add_all.assert_not_called()

    # Case B: Delete Data Tidak Ada (Return False)
    # Setup mock agar execute mengembalikan hasil kosong
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    deleted = await repo.delete("hantu_id")
    assert deleted is False

# --- 5. FIX SCHEME (Abstract Methods - 65% -> 100%) ---
@pytest.mark.asyncio
async def test_scheme_failures():
    # Case A: Token Invalid/Rusak
    with patch("std_pack.infrastructure.security.scheme.TokenHelper") as MockHelper:
        # Simulasi decode error
        MockHelper.return_value.decode_token.side_effect = ValueError("Boom")
        
        with pytest.raises(UnauthorizedError):
            get_current_token_payload("token_rusak")

    # Case B: get_current_user Abstract Call
    # Fungsi ini harusnya di-override di App level, tapi kita panggil base-nya
    with pytest.raises(NotImplementedError):
        await get_current_user({})