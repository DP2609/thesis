from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use a new database file
DB_FILE = "thesis.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///./{DB_FILE}"

def database_exists():
    """Check if database file exists and has tables"""
    if not os.path.exists(DB_FILE):
        return False
    
    # Check if database has tables
    try:
        temp_engine = create_engine(SQLALCHEMY_DATABASE_URL)
        inspector = inspect(temp_engine)
        tables = inspector.get_table_names()
        return len(tables) > 0
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return False

# Create engine with logging enabled
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