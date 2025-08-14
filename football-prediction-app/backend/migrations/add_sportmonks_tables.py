"""
Migration script to add SportMonks tables to the database
Run this script to create the new tables for SportMonks data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sportmonks_models import (
    SportMonksLeague, SportMonksTeam, SportMonksFixture,
    SportMonksPrediction, SportMonksValueBet, SportMonksOdds,
    SportMonksLiveData, SportMonksPlayer, SportMonksStanding
)
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sportmonks_tables():
    """Create all SportMonks tables"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create tables
            logger.info("Creating SportMonks tables...")
            
            # Import all models to ensure they're registered
            models = [
                SportMonksLeague, SportMonksTeam, SportMonksFixture,
                SportMonksPrediction, SportMonksValueBet, SportMonksOdds,
                SportMonksLiveData, SportMonksPlayer, SportMonksStanding
            ]
            
            # Create all tables
            db.create_all()
            
            logger.info("SportMonks tables created successfully!")
            
            # Verify tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            sportmonks_tables = [t for t in tables if t.startswith('sportmonks_')]
            logger.info(f"Created {len(sportmonks_tables)} SportMonks tables:")
            for table in sportmonks_tables:
                logger.info(f"  - {table}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating SportMonks tables: {str(e)}")
            return False

def drop_sportmonks_tables():
    """Drop all SportMonks tables (use with caution!)"""
    app = create_app()
    
    with app.app_context():
        try:
            from sqlalchemy import text, inspect
            
            # Get all SportMonks tables using inspector (safer approach)
            inspector = inspect(db.engine)
            all_tables = inspector.get_table_names()
            tables = [t for t in all_tables if t.startswith('sportmonks_')]
            
            if not tables:
                logger.info("No SportMonks tables found to drop")
                return True
            
            logger.warning(f"Dropping {len(tables)} SportMonks tables...")
            
            # Drop each table using parameterized query
            for table in tables:
                # Validate table name to prevent injection
                if not re.match(r'^sportmonks_[a-zA-Z0-9_]+$', table):
                    logger.error(f"Invalid table name format: {table}")
                    continue
                    
                # Use SQLAlchemy's table reflection for safe dropping
                try:
                    table_obj = db.Table(table, db.metadata, autoload_with=db.engine)
                    table_obj.drop(db.engine)
                    logger.info(f"  - Dropped {table}")
                except Exception as e:
                    logger.error(f"  - Failed to drop {table}: {str(e)}")
            
            db.session.commit()
            logger.info("All SportMonks tables dropped successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error dropping SportMonks tables: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage SportMonks database tables")
    parser.add_argument('action', choices=['create', 'drop'], 
                        help='Action to perform: create or drop tables')
    parser.add_argument('--force', action='store_true',
                        help='Force action without confirmation')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        success = create_sportmonks_tables()
        sys.exit(0 if success else 1)
    
    elif args.action == 'drop':
        if not args.force:
            response = input("Are you sure you want to drop all SportMonks tables? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Operation cancelled")
                sys.exit(0)
        
        success = drop_sportmonks_tables()
        sys.exit(0 if success else 1)