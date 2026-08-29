"""Small script to run the users importer locally (without Celery).

Usage:
    python api/scripts/run_users_importer.py

This will look for `./exports/users/latest.json` or `./exports/users/users_*.json` and
invoke the importer synchronously using the workers DB session.
"""
from pathlib import Path
from workers.tasks.users_importer import import_users_sync


def main():
    result = import_users_sync()
    print("Users importer result:")
    print(result)


if __name__ == "__main__":
    main()
