"""
Role Based Access Control (RBAC).
Mendukung pengecekan permission dinamis.
"""
from typing import Annotated
from fastapi import Depends
from .scheme import get_current_user, IAuthUser

# Import Custom Exception
from std_pack.domain.exceptions import ForbiddenError, UnauthorizedError

class PermissionDependency:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(self, user: Annotated[IAuthUser, Depends(get_current_user)]):
        
        if not user.is_active:
             # Ini domain rule: User tidak aktif tidak boleh akses
             raise UnauthorizedError("Inactive user")

        # Fallback Logic: Cek roles
        if hasattr(user, "roles") and self.required_permission not in user.roles:
             raise ForbiddenError(f"Missing permission: {self.required_permission}")
             
        # Smart Logic (jika ada method has_permission)
        if hasattr(user, "has_permission"):
            if not await user.has_permission(self.required_permission): # type: ignore
                raise ForbiddenError(f"Missing permission: {self.required_permission}")