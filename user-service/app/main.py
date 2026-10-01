from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from app.database import engine, get_db
from app import models, schemas, security

# Automatically initialize tables on start
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Service")

# Setup default OAuth2 security scheme pointing to the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@app.get("/health")
def health_check():
    return {"status": "ok"}

# --- Endpoint: POST /register ---
@app.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Evaluate whether the incoming target email exists in the database
    existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user account with this email address already exists."
        )
    
    # 2. Encrypt the incoming user password string
    hashed_pass = security.hash_password(user_in.password)
    
    # 3. Initialize the database object matching structural schemas
    new_user = models.User(
        email=user_in.email,
        password_hash=hashed_pass,
        first_name=user_in.first_name,
        last_name=user_in.last_name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- Endpoint: POST /login ---
@app.post("/login", response_model=schemas.Token)
def login_user(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    # 1. Fetch user by email context
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials."
        )
    
    # 2. Check cleartext against hash stored in database records
    if not security.verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials."
        )
    
    # 3. Create access token payload map
    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Endpoint: GET /me ---
@app.get("/me", response_model=schemas.UserOut)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authorization credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the inbound JWT authentication header
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    # Look up user database identity reference mapping string values
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

