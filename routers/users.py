from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from schemas import auth
from schemas import user as user_schema
from models import models
from utils.utils import hash_password, verify_password
from utils.auth import create_access_token, get_current_user, oauth2_scheme
import crud.user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=user_schema.UserOut)
def register(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    existing = crud.user.get_user(user, db)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(user.password)
    new_user = crud.user.create_user(user, db, hashed)
    return new_user


@router.post("/login", response_model=auth.Token)
def login(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.user.get_user(user, db)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Include role in token payload for frontend role checks
    token = create_access_token({"user_id": db_user.id, "role": db_user.role})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=user_schema.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # если токен уже отозван — ничего страшного
    existing = db.query(models.RevokedToken).filter(models.RevokedToken.token == token).first()
    if existing:
        return {"detail": "Already logged out"}
    revoked = models.RevokedToken(token=token)
    db.add(revoked)
    db.commit()
