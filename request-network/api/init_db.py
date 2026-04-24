#!/usr/bin/env python3
"""
Initialize Request Network database and create default admin user
This should be run after alembic migrations are applied
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from setup.initialization import initialize_database

if __name__ == "__main__":
    success = initialize_database()
    sys.exit(0 if success else 1)
