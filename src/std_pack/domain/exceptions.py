"""
Domain Custom exceptions Module
mendefinisikan base exceptions untuk error spesifik domain logic. 
agnostik terhadap HTTP atau response
"""

from typing import Any

class DomainException(Exception):
    """
    Base Class untuk semua error domain.
    """
    def __init__(
            self,
            message: str = "Domain error occurred", 
            code: str = "DOMAIN_ERROR" 
    ):
        self.message = message
        self.code = code
        super().__init__(self.message)

class EntityNotFoundError(DomainException):
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            message=f"{entity_name} dengan id {entity_id} tidak ditemukan",
            code=f"{entity_name.upper()}_NOT_FOUND"
        )

class EntityAlreadyExistsError(DomainException):
    def __init__(self, entity_name: str, field: str, value: Any):
        super().__init__(
            message=f"{entity_name} dengan {field}='{value}' sudah ada",
            code=f"{entity_name.upper()}_ALREADY_EXISTS"
        )

class BusinessRuleViolationError(DomainException):
    def __init__(self, message: str):
        super().__init__(message, code="BUSINESS_RULE_VIOLATION")

class UnauthorizedError(DomainException):
    def __init__(self, message: str = "Unauthorized domain operation"):
        super().__init__(message, code="DOMAIN_UNAUTHORIZED")

# Tambahkan class ini di domain/exceptions.py
class ForbiddenError(DomainException):
    """
    Error ketika user terautentikasi tapi tidak punya izin akses.
    (HTTP 403 equivalent)
    """
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, code="ACCESS_FORBIDDEN")    

class TooManyRequestsError(DomainException):
    def __init__(self, retry_after: int):
        super().__init__(
            message=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            code="RATE_LIMIT_EXCEEDED"
        )
        self.retry_after = retry_after            