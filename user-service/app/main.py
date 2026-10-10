import jwt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas, security
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Service")
bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized(detail: str = "Invalid or missing token"):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    if creds is None:
        raise unauthorized()
    try:
        payload = security.decode_access_token(creds.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized()
    user = db.get(models.User, user_id)
    if user is None:
        raise unauthorized()
    return user


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/register", response_model=schemas.UserOut,
          status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = models.User(
        email=email,
        name=payload.name,
        hashed_password=security.hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two requests raced past the check above
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(user)
    return user


@app.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.email == payload.email.lower()
    ).first()
    # same message for unknown email and wrong password, so attackers can't probe emails
    if user is None or not security.verify_password(payload.password, user.hashed_password):
        raise unauthorized("Incorrect email or password")
    return schemas.Token(access_token=security.create_access_token(user.id))


@app.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user
#this is the dumy content or comment
