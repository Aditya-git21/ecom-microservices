import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt

# Read configurations directly from the environment variables
SECRET_KEY = os.getenv("JWT_SECRET")
ACCESS_TOKEN_EXPIRE_MINUTES_STR = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

# Strict check: Fail immediately if the variables are missing
if not SECRET_KEY:
    raise ValueError("CRITICAL ERROR: JWT_SECRET environment variable is missing!")
if not ACCESS_TOKEN_EXPIRE_MINUTES_STR:
    raise ValueError("CRITICAL ERROR: ACCESS_TOKEN_EXPIRE_MINUTES environment variable is missing!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(ACCESS_TOKEN_EXPIRE_MINUTES_STR)

# --- Password Management Processing ---
def hash_password(password: str) -> str:
    """Hashes a clear text password using secure bcrypt salting."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that a plain text password matches a given hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# --- Token Creation Processing ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates an encrypted JWT access token string containing payload definitions."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

