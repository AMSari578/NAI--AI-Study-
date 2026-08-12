from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models as m
from app.modules.auth import schemas as s
from app.db.session import get_db
from app.core.security import create_token, current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=s.Token, status_code=201)
def register(body: s.Register, db: Session = Depends(get_db)):
    if db.query(m.User).filter(func.lower(m.User.email) == body.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    user = m.User(name=body.name.strip(), email=body.email.lower(), password_hash=hash_password(body.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_token(user.id), "user": user}


@router.post("/login", response_model=s.Token)
def login(body: s.Login, db: Session = Depends(get_db)):
    user = db.query(m.User).filter(func.lower(m.User.email) == body.email.lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(user.id), "user": user}


@router.get("/me", response_model=s.UserOut)
def me(user=Depends(current_user)):
    return user


@router.post("/logout", status_code=204)
def logout(_=Depends(current_user)):
    return None
