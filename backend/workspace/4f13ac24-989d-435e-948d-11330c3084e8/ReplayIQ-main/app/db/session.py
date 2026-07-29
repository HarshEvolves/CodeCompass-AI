from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create the engine instance.
# pool_pre_ping=True issues a test SELECT 1 query when retrieving a connection from the pool
# to make sure the database is alive before handing the connection to the application.
engine = create_engine(
    settings.sql_database_url,
    pool_pre_ping=True
)

# SessionLocal is configured as a factory for SQLAlchemy Session instances.
# autocommit=False and autoflush=False give us explicit control over transaction boundaries.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
