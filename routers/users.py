from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from db.database import get_db
from schemas import user as user_schema
from schemas.auth import Token, RefreshRequest
from models import models
from utils.utils import hash_password, verify_password
from utils.auth import get_current_user, oauth2_scheme
from services import auth_service
import crud.user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=user_schema.UserOut)
def register(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    if crud.user.get_user(user, db):
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed = hash_password(user.password)
    return crud.user.create_user(user, db, hashed)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    class UsernameAdapter:
        username = form_data.username

    db_user = crud.user.get_user(UsernameAdapter(), db)
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = auth_service.create_access_token(db_user)
    refresh_token = auth_service.create_refresh_token(db, db_user)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    user, new_refresh = auth_service.rotate_refresh_token(db, body.refresh_token)
    access_token = auth_service.create_access_token(user)
    return {"access_token": access_token, "refresh_token": new_refresh, "token_type": "bearer"}


@router.get("/me", response_model=user_schema.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(
    body: RefreshRequest,
    access_token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    auth_service.logout(db, access_token, body.refresh_token)
    return {"detail": "Logged out"}
