from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from models import models
import crud.admin_user
from utils.role import role_required
from schemas import user as user_schema

router = APIRouter(prefix="/admin", tags=["Admin"])

# Dependency that ensures admin role
admin_dependency = role_required("admin")

@router.get("/users", response_model=list[user_schema.UserOut])
def list_users(db: Session = Depends(get_db), _: models.User = Depends(admin_dependency)):
    return crud.admin_user.get_all_users(db)

@router.put("/users/{user_id}/role", response_model=user_schema.UserOut)
def change_user_role(user_id: int, role_update: user_schema.RoleUpdate, db: Session = Depends(get_db), _: models.User = Depends(admin_dependency)):
    user = crud.admin_user.get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if role_update.role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    return crud.admin_user.update_user_role(user, role_update.role, db)
