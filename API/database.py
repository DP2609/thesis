from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Use a new database file
DB_FILE = "thesis.db"
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

SQLALCHEMY_DATABASE_URL = f"sqlite:///./{DB_FILE}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=True  # Enable SQL logging for debugging
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 