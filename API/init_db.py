from database import engine, get_db, database_exists
import models
import security
from sqlalchemy.orm import Session
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_user(db: Session):
    """Create admin user if it doesn't exist"""
    # Check if admin user exists
    admin = db.query(models.User).filter(models.User.email == "admin@example.com").first()
    if not admin:
        admin_user = models.User(
            email="admin@example.com",
            username="admin",
            hashed_password=security.get_password_hash("admin123"),
            is_active=True,
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        logger.info("Admin user created successfully!")
    else:
        logger.info("Admin user already exists!")
        
    # Verify the admin user was created correctly
    admin = db.query(models.User).filter(models.User.email == "admin@example.com").first()
    if admin and admin.is_admin:
        logger.info("Verified admin user has is_admin=True")
    else:
        logger.error("Admin user verification failed!")

def init_db():
    try:
        # Check if database already exists and has tables
        if database_exists():
            logger.info("Database already exists with tables, skipping initialization")
            # Just verify admin user exists
            db = next(get_db())
            create_admin_user(db)
            db.close()
            return

        logger.info("Initializing new database...")
        # Create all tables
        models.Base.metadata.create_all(bind=engine)
        logger.info("Created all tables successfully")
        
        # Create admin user
        db = next(get_db())
        create_admin_user(db)
        db.close()
            
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()