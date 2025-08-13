#!/usr/bin/env python3
"""
Database initialization script for production
Run this after the database is created and available
"""
import sys
from app import create_app, db

def init_database():
    """Initialize database tables"""
    try:
        app = create_app('production')
        with app.app_context():
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully!")
            return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)