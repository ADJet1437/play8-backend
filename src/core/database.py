import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Get database URL from environment variable, with fallback
# For local development (connecting from host to Docker): use port 5444
# For Docker (container to container): use service name 'db' and port 5432
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://play8:play8@localhost:5444/play8")

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database function
def init_database():
    """Initialize database tables"""
    # Import all models to ensure they're registered with Base

    Base.metadata.create_all(bind=engine)
