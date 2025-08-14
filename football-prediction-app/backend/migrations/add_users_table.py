"""
Migration script to add users table for authentication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from auth import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_users_table():
    """Create users table for authentication"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Creating users table...")
            
            # Create the table
            User.__table__.create(db.engine, checkfirst=True)
            
            logger.info("Users table created successfully!")
            
            # Verify table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'users' in tables:
                logger.info("✓ Users table confirmed in database")
                
                # Get column info
                columns = inspector.get_columns('users')
                logger.info(f"Table has {len(columns)} columns:")
                for col in columns:
                    logger.info(f"  - {col['name']} ({col['type']})")
            else:
                logger.error("Users table not found after creation!")
                return False
            
            # Create default admin user if none exists
            from auth import AuthService
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
                logger.info("Creating default admin user...")
                admin = User(username='admin', email='admin@example.com', is_admin=True)
                admin.set_password('changeme123!')  # CHANGE THIS IN PRODUCTION
                admin.generate_api_key()
                db.session.add(admin)
                db.session.commit()
                logger.info("Default admin user created (username: admin, password: changeme123!)")
                logger.warning("⚠️  CHANGE THE DEFAULT ADMIN PASSWORD IMMEDIATELY!")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating users table: {str(e)}")
            db.session.rollback()
            return False

def drop_users_table():
    """Drop users table (use with caution!)"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.warning("Dropping users table...")
            
            User.__table__.drop(db.engine, checkfirst=True)
            
            logger.info("Users table dropped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error dropping users table: {str(e)}")
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage users database table")
    parser.add_argument('action', choices=['create', 'drop'], 
                        help='Action to perform: create or drop table')
    parser.add_argument('--force', action='store_true',
                        help='Force action without confirmation')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        success = create_users_table()
        sys.exit(0 if success else 1)
    
    elif args.action == 'drop':
        if not args.force:
            response = input("Are you sure you want to drop the users table? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Operation cancelled")
                sys.exit(0)
        
        success = drop_users_table()
        sys.exit(0 if success else 1)