from std_pack.domain.value_objects import BaseValueObject

class Money(BaseValueObject):
    amount: int
    currency: str

def test_value_object_equality():
    m1 = Money(amount=100, currency="IDR")
    m2 = Money(amount=100, currency="IDR")
    m3 = Money(amount=200, currency="IDR")
    
    assert m1 == m2  # Test __eq__ True path
    assert m1 != m3  # Test __eq__ False path (value beda)
    assert m1 != "Just String" # Test __eq__ False path (tipe beda)