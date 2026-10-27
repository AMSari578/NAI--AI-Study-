from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .config import settings
from ..db.session import get_db
from ..models import User

# PBKDF2 avoids bcrypt's 72-byte password truncation while remaining a
# deliberately slow, salted password KDF supported by Passlib.
pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)
def hash_password(value: str): return pwd.hash(value)
def verify_password(value: str, hashed: str): return pwd.verify(value, hashed)
def create_token(user_id: int):
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.jwt_secret, algorithm="HS256")
def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    if not credentials: raise HTTPException(401, "Authentication required")
    try: user_id = int(jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])["sub"])
    except (JWTError, KeyError, ValueError): raise HTTPException(401, "Invalid or expired session")
    user = db.get(User, user_id)
    if not user: raise HTTPException(401, "User no longer exists")
    return user
