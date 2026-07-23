"""Standalone seed script runner."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.seed import seed_database

if __name__ == "__main__":
    seed_database()
