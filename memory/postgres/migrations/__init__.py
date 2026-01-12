"""Database migration scripts for The Hive."""

import os
from typing import Optional

from ..client import PostgresClient


def run_migrations(database_url: Optional[str] = None) -> None:
    """Run database migrations.

    Args:
        database_url: PostgreSQL connection URL
    """
    client = PostgresClient(database_url)
    print("Creating database tables...")
    client.create_tables()
    print("Migrations completed successfully!")


def rollback_migrations(database_url: Optional[str] = None) -> None:
    """Rollback database migrations (drop all tables).

    WARNING: This will delete all data!

    Args:
        database_url: PostgreSQL connection URL
    """
    confirm = input("Are you sure you want to drop all tables? (yes/no): ")
    if confirm.lower() != "yes":
        print("Rollback cancelled.")
        return

    client = PostgresClient(database_url)
    print("Dropping database tables...")
    client.drop_tables()
    print("Rollback completed!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migrations()
    else:
        run_migrations()
