"""PostgreSQL client wrapper for The Hive."""

import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker, Session

from .models import Base


class PostgresClient:
    """PostgreSQL client with connection pooling."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize PostgreSQL client.

        Args:
            database_url: PostgreSQL connection URL. If None, reads from env vars.
        """
        if database_url is None:
            database_url = self._get_database_url()

        self.engine: Engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

    def _get_database_url(self) -> str:
        """Build database URL from environment variables."""
        return (
            f"postgresql://{os.getenv('POSTGRES_USER', 'hive_user')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'hive_password')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB', 'the_hive')}"
        )

    def create_tables(self) -> None:
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all tables from the database."""
        Base.metadata.drop_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup.

        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """Check database connection health.

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False


# Global client instance
_client: Optional[PostgresClient] = None


def get_postgres_client() -> PostgresClient:
    """Get global PostgreSQL client instance.

    Returns:
        PostgreSQL client
    """
    global _client
    if _client is None:
        _client = PostgresClient()
    return _client
