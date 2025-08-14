#!/usr/bin/env python
"""
Scheduler Runner for Football Prediction App
Runs background tasks for fetching and storing API data
"""

import os
import sys
import time
import logging
from datetime import datetime
import secrets

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure we're in production mode for the scheduler
os.environ['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'production')
os.environ['ENABLE_SCHEDULER'] = 'true'

def generate_internal_api_key():
    """Generate a secure internal API key if not already set"""
    if not os.environ.get('INTERNAL_API_KEYS'):
        # Generate a secure key for internal use
        api_key = secrets.token_urlsafe(32)
        os.environ['INTERNAL_API_KEYS'] = api_key
        logger.info(f"Generated internal API key for scheduler: {api_key[:8]}...")
        return api_key
    return os.environ.get('INTERNAL_API_KEYS').split(',')[0]

def run_scheduler():
    """Run the scheduler service"""
    try:
        from app import create_app
        from scheduler import DataScheduler
        from sportmonks_scheduler import sportmonks_scheduler
        
        # Generate internal API key for scheduler to use
        internal_api_key = generate_internal_api_key()
        
        # Create Flask app
        logger.info("Creating Flask app for scheduler...")
        app = create_app()
        
        with app.app_context():
            # Initialize database tables if needed
            from models import db
            try:
                db.create_all()
                logger.info("Database tables verified/created")
            except Exception as e:
                logger.error(f"Error creating database tables: {str(e)}")
            
            # Initialize regular Football Data scheduler
            logger.info("Initializing Football Data scheduler...")
            football_scheduler = DataScheduler()
            football_scheduler.init_app(app)
            
            # Initialize SportMonks scheduler
            logger.info("Initializing SportMonks scheduler...")
            sportmonks_scheduler.init_app(app)
            
            # Start the Football Data scheduler
            logger.info("Starting Football Data scheduler...")
            football_scheduler.start()
            
            # Start the SportMonks scheduler
            logger.info("Starting SportMonks scheduler...")
            if not sportmonks_scheduler.scheduler.running:
                sportmonks_scheduler.start()
                logger.info("SportMonks scheduler started")
            
            # Run initial data sync after a short delay
            logger.info("Waiting 30 seconds before initial data sync...")
            time.sleep(30)
            
            logger.info("Running initial data sync...")
            try:
                # Only run if database is empty
                from models import Team, Match
                team_count = Team.query.count()
                match_count = Match.query.count()
                
                if team_count == 0 or match_count == 0:
                    logger.info(f"Database appears empty (teams: {team_count}, matches: {match_count}). Running initial sync...")
                    football_scheduler.fetch_historical_data()
                    sportmonks_scheduler.update_upcoming_fixtures()
                    logger.info("Initial data sync completed")
                else:
                    logger.info(f"Database already has data (teams: {team_count}, matches: {match_count}). Skipping initial sync.")
            except Exception as e:
                logger.error(f"Error during initial sync: {str(e)}")
            
            # Log scheduled jobs
            logger.info("\n=== Scheduled Jobs ===")
            logger.info("Football Data Scheduler:")
            for job in football_scheduler.scheduler.get_jobs():
                logger.info(f"  - {job.name}: {job.trigger}")
            
            logger.info("\nSportMonks Scheduler:")
            for job in sportmonks_scheduler.scheduler.get_jobs():
                logger.info(f"  - {job.name}: {job.trigger}")
            logger.info("===================\n")
            
            # Keep the process running
            logger.info("Scheduler service is running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(60)  # Sleep for 1 minute
                    
                    # Log heartbeat every hour
                    if datetime.now().minute == 0:
                        logger.info("Scheduler heartbeat - service is running")
                        
                        # Check scheduler health
                        if not football_scheduler.scheduler.running:
                            logger.error("Football scheduler stopped! Attempting restart...")
                            football_scheduler.start()
                        
                        if not sportmonks_scheduler.scheduler.running:
                            logger.error("SportMonks scheduler stopped! Attempting restart...")
                            sportmonks_scheduler.start()
                            
            except KeyboardInterrupt:
                logger.info("Scheduler service stopped by user")
                football_scheduler.shutdown()
                if sportmonks_scheduler.scheduler.running:
                    sportmonks_scheduler.stop()
                sys.exit(0)
                
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_scheduler()