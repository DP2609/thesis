from database import engine, get_db
import models
import security
from sqlalchemy.orm import Session
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    try:
        logger.info("Dropping all tables...")
        models.Base.metadata.drop_all(bind=engine)
        
        logger.info("Creating all tables...")
        models.Base.metadata.create_all(bind=engine)
        
        logger.info("Creating admin user...")
        db = next(get_db())
        
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
            
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 