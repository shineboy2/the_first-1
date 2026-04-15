#!/usr/bin/env python3
"""
Seed database with initial data for development and production

Usage:
    export PYTHONPATH="/workspaces/the_first:${PYTHONPATH}"
    python manage_db.py seed --network response
    python manage_db.py seed --network request
    python manage_db.py seed
"""

import sys
from pathlib import Path
from uuid import uuid4

# Ensure proper path setup
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "response-network" / "api"))
sys.path.insert(0, str(PROJECT_ROOT / "request-network" / "api"))

import click
from sqlalchemy.orm import Session
from sqlalchemy import select


def seed_response_network():
    """Seed Response Network with initial data"""
    from db.session import SessionLocal
    from models.user import User
    from core.hashing import get_password_hash
    
    click.echo("🌱 Seeding Response Network...")
    db = SessionLocal()
    
    try:
        # Seed Profile Types first to satisfy Foreign Keys
        seed_profile_types(db)

        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            click.echo("  ℹ Admin user already exists, skipping...")
        else:
            # Create admin user
            admin_user = User(
                id=uuid4(),
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin@123456"),
                full_name="System Administrator",
                profile_type="admin",
                is_active=True,
                is_admin=True,
                daily_request_limit=10000,
                monthly_request_limit=100000,
                max_results_per_request=5000,
                allowed_indices=["*"],
            )
            
            db.add(admin_user)
            db.commit()
            click.echo(f"  ✓ Created admin user: admin (password: admin@123456)")
        
        # Create sample users
        sample_users = [
            {
                "username": "user_basic",
                "email": "basic@example.com",
                "password": "user@123456",
                "profile_type": "basic",
                "daily_limit": 100,
                "monthly_limit": 2000,
            },
            {
                "username": "user_premium",
                "email": "premium@example.com",
                "password": "user@123456",
                "profile_type": "premium",
                "daily_limit": 1000,
                "monthly_limit": 20000,
            },
        ]
        
        created_count = 0
        for user_data in sample_users:
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if not existing:
                user = User(
                    id=uuid4(),
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["username"].replace("_", " ").title(),
                    profile_type=user_data["profile_type"],
                    is_active=True,
                    is_admin=False,
                    daily_request_limit=user_data["daily_limit"],
                    monthly_request_limit=user_data["monthly_limit"],
                    max_results_per_request=1000,
                    allowed_indices=["*"],
                )
                db.add(user)
                created_count += 1
        
        if created_count > 0:
            db.commit()
            click.echo(f"  ✓ Created {created_count} sample users")
        else:
            click.echo(f"  ℹ Sample users already exist")
        
        click.secho("✅ Response Network seeded successfully!", fg="green")
        
    except Exception as e:
        db.rollback()
        click.secho(f"  ✗ Error: {e}", fg="red", err=True)
        raise
    finally:
        db.close()

def seed_profile_types(db):
    """Seed initial profile types"""
    from models.profile_type_config import ProfileTypeConfig
    
    click.echo("  🔧 Seeding profile types...")
    
    profiles = [
        {
            "name": "admin",
            "display_name": "Administrator",
            "description": "System Administrator with full access",
            "permissions": {
                "allowed_request_types": ["*"],
                "blocked_request_types": [],
                "max_results_per_request": 10000
            },
            "daily_limit": 10000,
            "monthly_limit": 100000,
            "rate_limit_min": 1000,
            "rate_limit_hour": 5000,
            "is_builtin": True
        },
        {
            "name": "basic",
            "display_name": "Basic User",
            "description": "Standard user with limited access",
            "permissions": {
                "allowed_request_types": ["HotelSearch", "FlightSearch"],
                "blocked_request_types": [],
                "max_results_per_request": 100
            },
            "daily_limit": 100,
            "monthly_limit": 2000,
            "rate_limit_min": 60,
            "rate_limit_hour": 300,
            "is_builtin": True
        },
        {
            "name": "premium",
            "display_name": "Premium User",
            "description": "Premium user with higher limits",
            "permissions": {
                "allowed_request_types": ["*"],
                "blocked_request_types": [],
                "max_results_per_request": 1000
            },
            "daily_limit": 1000,
            "monthly_limit": 20000,
            "rate_limit_min": 300,
            "rate_limit_hour": 1500,
            "is_builtin": True
        }
    ]
    
    for p_data in profiles:
        existing = db.query(ProfileTypeConfig).filter(ProfileTypeConfig.name == p_data["name"]).first()
        if not existing:
            profile = ProfileTypeConfig(
                name=p_data["name"],
                display_name=p_data["display_name"],
                description=p_data["description"],
                permissions=p_data["permissions"],
                daily_request_limit=p_data["daily_limit"],
                monthly_request_limit=p_data["monthly_limit"],
                rate_limit_per_minute=p_data["rate_limit_min"],
                rate_limit_per_hour=p_data["rate_limit_hour"],
                is_active=True,
                is_builtin=p_data["is_builtin"]
            )
            db.add(profile)
            click.echo(f"    + Created profile type: {p_data['name']}")
    
    db.commit()


def seed_request_network():
    """Initialize Request Network (users are imported from Response Network)"""
    click.echo("🌱 Initializing Request Network...")
    click.echo("  ℹ Request Network users are imported from Response Network")
    
    try:
        from db.session import SessionLocal
        db = SessionLocal()
        db.close()
        click.secho("✅ Request Network initialized successfully!", fg="green")
    except Exception as e:
        click.secho(f"  ✗ Error: {e}", fg="red", err=True)
        raise


@click.group()
def cli():
    """Database management commands"""
    pass


@cli.command()
@click.option(
    "--network",
    type=click.Choice(["response", "request", "both"]),
    default="both",
    help="Which network to seed (default: both)",
)
def seed(network):
    """Seed database with initial data"""
    try:
        if network in ["response", "both"]:
            seed_response_network()
        
        if network in ["request", "both"]:
            seed_request_network()
        
    except ImportError as e:
        click.secho(f"❌ Import error: {e}", fg="red", err=True)
        click.echo("Make sure PYTHONPATH includes the project root:", err=True)
        click.echo('  export PYTHONPATH="/workspaces/the_first:${PYTHONPATH}"', err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--network",
    type=click.Choice(["response", "request", "both"]),
    default="both",
    help="Which network to drop",
)
def drop_all(network):
    """Drop all data (WARNING: Destructive!)"""
    if not click.confirm("⚠️  This will DELETE ALL DATA. Continue?"):
        click.echo("Aborted.")
        return
    
    try:
        if network in ["response", "both"]:
            click.echo("🗑️  Dropping all tables from Response Network...")
            from db.session import SessionLocal
            db = SessionLocal()
            from db.base import Base
            
            # Drop all tables
            Base.metadata.drop_all(db.get_bind())
            db.close()
            click.echo("  ✓ Response Network cleared")
        
        if network in ["request", "both"]:
            click.echo("🗑️  Dropping all tables from Request Network...")
            # Switch context for Request Network
            import importlib
            import sys
            
            # Remove response network from modules
            modules_to_remove = [m for m in sys.modules if 'response' in m and 'models' in m or 'db' in m]
            for m in modules_to_remove:
                del sys.modules[m]
            
            from db.session import SessionLocal as RequestSessionLocal
            db = RequestSessionLocal()
            from db.base import Base as RequestBase
            
            RequestBase.metadata.drop_all(db.get_bind())
            db.close()
            click.echo("  ✓ Request Network cleared")
        
        click.secho("✅ Drop complete!", fg="green")
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
