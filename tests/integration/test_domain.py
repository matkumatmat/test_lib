import pytest
from uuid import uuid4
from std_pack.domain.entities import BaseEntity, SoftDeleteMixin
from std_pack.domain.exceptions import DomainException

# --- DUMMY CLASS ---
class User(BaseEntity, SoftDeleteMixin):
    name: str

def test_entity_equality():
    """Test bahwa dua entity dianggap sama jika ID-nya sama."""
    uid = uuid4()
    user1 = User(id=uid, name="A")
    user2 = User(id=uid, name="B") # Nama beda, tapi ID sama
    user3 = User(id=uuid4(), name="A") # Nama sama, ID beda
    
    assert user1 == user2
    assert user1 != user3
    assert user1 != "Not An Entity"

def test_soft_delete_logic():
    """Test logika mark_deleted dan restore."""
    user = User(name="Test")
    assert user.is_deleted is False
    assert user.deleted_at is None

    # 1. Delete
    user.mark_deleted()
    assert user.is_deleted is True
    assert user.deleted_at is not None

    # 2. Restore
    user.restore()
    assert user.is_deleted is False
    assert user.deleted_at is None

def test_domain_exception():
    """Test instansiasi exception custom."""
    exc = DomainException("Something wrong", code="ERR_01")
    assert str(exc) == "Something wrong"
    assert exc.code == "ERR_01"