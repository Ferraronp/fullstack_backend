from fastapi import Depends, HTTPException, status
from utils.auth import get_current_user
from models import models

def role_required(required_role: str):
    async def dependency(current_user: models.User = Depends(get_current_user)):
        # Simple hierarchy: admin > user > guest
        role_hierarchy = {"guest": 0, "user": 1, "admin": 2}
        user_role = current_user.role if hasattr(current_user, "role") else "user"
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return current_user
    return dependency
