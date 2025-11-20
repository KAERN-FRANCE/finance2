"""
Script to initialize or reset the database.
Run this to create/recreate all database tables.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.models.database import Base, engine
from backend.utils.logger import log

def init_database():
    """Initialize the database by creating all tables."""
    try:
        log.info("Creating database tables...")

        # Drop all tables (optional - comment out if you want to preserve data)
        # Base.metadata.drop_all(bind=engine)
        # log.warning("All tables dropped")

        # Create all tables
        Base.metadata.create_all(bind=engine)

        log.info("Database tables created successfully!")
        log.info("Tables: " + ", ".join(Base.metadata.tables.keys()))

        return True
    except Exception as e:
        log.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize the database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables before creating (WARNING: deletes all data)"
    )
    args = parser.parse_args()

    if args.reset:
        log.warning("RESET flag set - all data will be deleted!")
        confirm = input("Are you sure? Type 'yes' to confirm: ")
        if confirm.lower() == "yes":
            Base.metadata.drop_all(bind=engine)
            log.warning("All tables dropped")
        else:
            log.info("Reset cancelled")
            sys.exit(0)

    success = init_database()
    sys.exit(0 if success else 1)
