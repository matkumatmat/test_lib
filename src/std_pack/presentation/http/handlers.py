"""
Global Exception Handlers.
Menerjemahkan Domain Exceptions menjadi HTTP Responses yang sesuai.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from std_pack.domain.exceptions import (
    DomainException,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    BusinessRuleViolationError,
    UnauthorizedError,
    ForbiddenError,
    TooManyRequestsError
)

async def domain_exception_handler(request: Request, exc: DomainException):
    """
    Handler default untuk semua DomainException.
    Otomatis memetakan tipe exception ke HTTP Status Code.
    """
    status_code = status.HTTP_400_BAD_REQUEST  # Default fallback
    
    match exc:
        case EntityNotFoundError():
            status_code = status.HTTP_404_NOT_FOUND
        case EntityAlreadyExistsError():
            status_code = status.HTTP_409_CONFLICT
        case UnauthorizedError():
            status_code = status.HTTP_401_UNAUTHORIZED
        case ForbiddenError():
            status_code = status.HTTP_403_FORBIDDEN
        case BusinessRuleViolationError():
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        case TooManyRequestsError():
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
            
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "path": request.url.path
            }
        },
    )


# Di main.py nanti
# from std_pack.infrastructure.web.exception_handlers import domain_exception_handler
# from std_pack.domain.exceptions import DomainException

# app.add_exception_handler(DomainException, domain_exception_handler)    