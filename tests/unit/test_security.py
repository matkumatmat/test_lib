# tests/unit/test_security.py
import pytest
from datetime import timedelta
from jose import JWTError
from unittest.mock import MagicMock

# 1. Import yang BENAR sesuai kode Anda
from std_pack.infrastructure.security.password import hash_password, verify_password
from std_pack.infrastructure.security.token import TokenHelper
from std_pack.infrastructure.security.obfuscation import IDObfuscator
from std_pack.infrastructure.security.rbac import PermissionDependency
from std_pack.domain.exceptions import ForbiddenError, UnauthorizedError

# --- TEST PASSWORD (Functions) ---
def test_password_hashing():
    plain = "rahasia123"
    
    # Hashing
    hashed = hash_password(plain)
    assert hashed != plain
    assert "$2b$" in hashed  # BCrypt signature
    
    # Verify
    assert verify_password(plain, hashed) is True
    assert verify_password("salah", hashed) is False

# --- TEST TOKEN (Helper Class) ---
def test_jwt_token_flow():
    # TokenHelper butuh 'settings' object. Kita Mock saja.
    mock_settings = MagicMock()
    mock_settings.SECRET_KEY = "super-secret-key"
    
    helper = TokenHelper(settings=mock_settings)
    
    user_id = "user_123"
    
    # 1. Create
    token = helper.create_access_token(user_id)
    assert isinstance(token, str)
    
    # 2. Decode
    payload = helper.decode_token(token)
    assert payload["sub"] == user_id
    assert "exp" in payload

    # 3. Invalid Token
    with pytest.raises(ValueError):
        helper.decode_token("invalid.token.here")

# --- TEST OBFUSCATION (IDObfuscator Class) ---
def test_id_obfuscation():
    # Test Class Obfuscator (bukan mask_email karena file obfuscation.py isinya class ini)
    # Kita butuh install 'sqids' dulu, atau pastikan mock jika library tidak ada
    # Asumsi sqids terinstall (sesuai prompt Anda)
    
    try:
        obfuscator = IDObfuscator(secret_salt="my-salt", min_length=8)
        
        original_id = 105
        
        # 1. Encode
        hashed = obfuscator.encode(original_id)
        assert isinstance(hashed, str)
        assert len(hashed) >= 8
        
        # 2. Decode
        decoded = obfuscator.decode(hashed)
        assert decoded == original_id
        
    except ImportError:
        pytest.skip("Library 'sqids' belum diinstall, skip test obfuscation.")

# --- TEST RBAC (PermissionDependency) ---
@pytest.mark.asyncio
async def test_rbac_dependency():
    # RBAC di kode Anda berbentuk FastAPI Dependency (__call__)
    # Dependency ini menerima 'user'. Kita harus mock user-nya.
    
    checker = PermissionDependency(required_permission="delete_user")
    
    # Skenario 1: User Inactive -> Error
    inactive_user = MagicMock()
    inactive_user.is_active = False
    
    with pytest.raises(UnauthorizedError):
        await checker(inactive_user)
        
    # Skenario 2: User Active, Tapi Roles Kurang -> Error
    active_user_no_perm = MagicMock()
    active_user_no_perm.is_active = True
    active_user_no_perm.roles = ["read_user"] # Gak punya 'delete_user'
    # Pastikan user tidak punya method has_permission agar fallback ke attribute check
    del active_user_no_perm.has_permission 
    
    with pytest.raises(ForbiddenError):
        await checker(active_user_no_perm)

    # Skenario 3: User Active, Roles Cukup -> Sukses (Tidak raise error)
    admin_user = MagicMock()
    admin_user.is_active = True
    admin_user.roles = ["read_user", "delete_user"]
    del admin_user.has_permission
    
    # Harusnya pass tanpa error
    await checker(admin_user)