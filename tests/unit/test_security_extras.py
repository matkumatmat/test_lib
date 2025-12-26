# tests/unit/test_security_extras.py

import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

# Imports Target Code
from std_pack.infrastructure.security.sanitization import InputSanitizer
from std_pack.infrastructure.security.rate_limit import RateLimiter
from std_pack.domain.exceptions import (
    TooManyRequestsError, 
    ForbiddenError, 
    UnauthorizedError
)
from std_pack.infrastructure.security.obfuscation import Obfuscator, IDObfuscator 
from std_pack.infrastructure.security.password import hash_password, verify_password
from std_pack.infrastructure.security.token import TokenHelper
from std_pack.infrastructure.security.rbac import PermissionDependency
from std_pack.infrastructure.security.scheme import get_current_user, get_current_token_payload

# ==========================================
# 1. TEST SANITIZATION
# ==========================================
def test_input_sanitizer():
    assert InputSanitizer.is_safe("Hello World") is True
    assert InputSanitizer.is_safe("1=1") is False
    assert InputSanitizer.is_safe("' OR '1'='1") is False
    assert InputSanitizer.is_safe("DROP TABLE users") is False
    assert InputSanitizer.is_safe("<script>alert(1)</script>") is False
    assert InputSanitizer.clean("Hello\x00World") == "HelloWorld"
    # Case Empty
    assert InputSanitizer.is_safe(None) is True # type: ignore

# ==========================================
# 2. TEST RATE LIMITER
# ==========================================
@pytest.mark.asyncio
async def test_rate_limiter_logic():
    limiter = RateLimiter(times=2, seconds=60)
    mock_request = MagicMock()
    mock_redis = AsyncMock() 
    mock_pipe = MagicMock()
    
    mock_pipe.incr = MagicMock()
    mock_pipe.ttl = MagicMock()
    mock_pipe.execute = AsyncMock(return_value=[1, 60]) 
    mock_redis.pipeline = MagicMock(return_value=mock_pipe)
    
    mock_request.state.redis = mock_redis
    mock_request.client.host = "127.0.0.1"
    mock_request.url.path = "/login"
    mock_request.method = "POST"
    
    # Case 1: Success
    await limiter(mock_request, None)
    
    # Case 2: Over Limit
    mock_pipe.execute = AsyncMock(return_value=[3, 50]) 
    with pytest.raises(TooManyRequestsError) as exc:
        await limiter(mock_request, None)
    assert exc.value.retry_after == 50

@pytest.mark.asyncio
async def test_rate_limiter_no_redis():
    limiter = RateLimiter()
    mock_request = MagicMock()
    mock_request.state.redis = None 
    await limiter(mock_request, None)

# ==========================================
# 3. TEST OBFUSCATION (SAPU BERSIH)
# ==========================================
def test_Obfuscator_masking():
    # Email Normal
    assert Obfuscator.mask_email("johndoe@example.com") == "j*****e@example.com"
    assert Obfuscator.mask_email("ab@c.com") == "a*@c.com" 
    
    # Email Edge Cases (Cover baris 66-67)
    assert Obfuscator.mask_email("invalid-email") == "invalid-email" 
    assert Obfuscator.mask_email(None) is None # type: ignore
    # Email aneh memancing Exception block
    assert Obfuscator.mask_email("double@@at.com") == "double@@at.com"

    # Phone Edge Cases (Cover baris 82)
    assert Obfuscator.mask_phone("081234567890") == "********7890"
    assert Obfuscator.mask_phone("123") == "***" 
    assert Obfuscator.mask_phone(None) == "***" # type: ignore

    # Credit Card Edge Cases (Cover baris 89, 93)
    assert Obfuscator.mask_credit_card("1234-5678-1234-5678") == "************5678"
    assert Obfuscator.mask_credit_card("123") == "***" 

    # General String
    res = Obfuscator.mask_string("secretpassword", visible_start=2, visible_end=2)
    assert res.startswith("se") and res.endswith("rd")
    assert Obfuscator.mask_string(None) == "" # type: ignore
    
    # Dict & Recursion (Cover baris 116-125)
    data = {
        "password": "secret",
        "email": "johndoe@example.com",
        "nested": {"token": "ey12345"}, # Recursion
        "phone": "0812345678",
        "mobile": "0812345678",
        "ktp": "1234567890",
        "ignored_int": 123 # Ignored type
    }
    cleaned = Obfuscator.obfuscate_dict(data)
    assert cleaned["password"] == "********"
    assert cleaned["email"] == "j*****e@example.com"
    assert cleaned["nested"]["token"] == "********"
    assert cleaned["phone"] == "******5678"
    assert cleaned["ktp"].startswith("12")

def test_id_obfuscator_missing_sqids():
    """Simulasi jika sqids tidak terinstall (Cover baris 17-20)"""
    # Kita patch module 'std_pack.infrastructure.security.obfuscation.Sqids' menjadi None
    with patch("std_pack.infrastructure.security.obfuscation.Sqids", None):
        with pytest.raises(ImportError):
            IDObfuscator()

def test_id_obfuscator_logic():
    # Test Init & Salt
    obfuscator = IDObfuscator(secret_salt="rahasia_negara", min_length=10)
    
    # Test Encode
    original_id = 12345
    hashed = obfuscator.encode(original_id)
    assert len(hashed) >= 10
    
    # Test Decode
    decoded_id = obfuscator.decode(hashed)
    assert decoded_id == original_id
    
    # Test Decode Invalid
    assert obfuscator.decode("hash#rusak") is None

# ==========================================
# 4. TEST AUTH & TOKEN
# ==========================================
def test_password_hashing():
    plain = "secret"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong", hashed) is False

def test_token_helper():
    mock_settings = MagicMock()
    mock_settings.SECRET_KEY = "test_secret"
    mock_settings.ALGORITHM = "HS256"
    mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    helper = TokenHelper(mock_settings)
    token = helper.create_access_token("user_123") 
    payload = helper.decode_token(token)
    assert payload["sub"] == "user_123"
    
    token_short = helper.create_access_token("user_456", expires_delta=timedelta(seconds=1))
    assert len(token_short) > 10
    
    with pytest.raises(ValueError):
        helper.decode_token("token.rusak.banget")

def test_auth_user_model():
    class ConcreteUser:
        def __init__(self, id, username, role):
            self.id = id
            self.username = username
            self.role = role
            self.is_active = True
            
    user = ConcreteUser(id=1, username="admin", role="superuser")
    assert user.id == 1

# ==========================================
# 5. TEST RBAC
# ==========================================
@pytest.mark.asyncio
async def test_rbac_dependency():
    dep = PermissionDependency(required_permission="admin_only")
    
    # Inactive
    user_inactive = MagicMock()
    user_inactive.is_active = False
    with pytest.raises(UnauthorizedError):
        await dep(user_inactive)
        
    # Guest
    user_guest = MagicMock()
    user_guest.is_active = True
    user_guest.roles = ["guest"]
    del user_guest.has_permission 
    with pytest.raises(ForbiddenError):
        await dep(user_guest)
        
    # Admin (Fallback)
    user_admin = MagicMock()
    user_admin.is_active = True
    user_admin.roles = ["guest", "admin_only"]
    del user_admin.has_permission 
    await dep(user_admin)

    # Smart Logic
    user_smart = MagicMock()
    user_smart.is_active = True
    del user_smart.roles 
    
    user_smart.has_permission = AsyncMock(return_value=True)
    await dep(user_smart) # Success
    
    user_smart.has_permission = AsyncMock(return_value=False)
    with pytest.raises(ForbiddenError):
        await dep(user_smart) # Failed

# ==========================================
# 6. TEST SCHEME
# ==========================================
@pytest.mark.asyncio
async def test_scheme_placeholders():
    with pytest.raises(NotImplementedError):
        await get_current_user({})
    
    with pytest.raises(UnauthorizedError):
        get_current_token_payload("token_ngawur")