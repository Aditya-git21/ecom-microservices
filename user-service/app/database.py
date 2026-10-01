import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Read the database connection URL from the system environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Strict check: Fail immediately if the variable is missing
if not DATABASE_URL:
    raise ValueError("CRITICAL ERROR: DATABASE_URL environment variable is missing!")

# Create the SQLAlchemy Engine
engine = create_engine(DATABASE_URL)

# Create the Session Local Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()

# Dependency injection function to handle database sessions per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

