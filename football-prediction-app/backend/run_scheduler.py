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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure we're in production mode for the scheduler
os.environ['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'production')
os.environ['ENABLE_SCHEDULER'] = 'true'

def run_scheduler():
    """Run the scheduler service"""
    try:
        from app import create_app
        from scheduler import FootballScheduler
        from sportmonks_scheduler import sportmonks_scheduler
        
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
            
            # Initialize regular scheduler
            logger.info("Initializing Football Data scheduler...")
            football_scheduler = FootballScheduler()
            football_scheduler.init_app(app)
            
            # Initialize SportMonks scheduler
            logger.info("Initializing SportMonks scheduler...")
            sportmonks_scheduler.init_app(app)
            
            # Run initial data sync
            logger.info("Running initial data sync...")
            try:
                # Fetch some initial data to populate the database
                football_scheduler.fetch_historical_data()
                sportmonks_scheduler.update_upcoming_fixtures()
                logger.info("Initial data sync completed")
            except Exception as e:
                logger.error(f"Error during initial sync: {str(e)}")
            
            # Start the SportMonks scheduler
            if not sportmonks_scheduler.scheduler.running:
                sportmonks_scheduler.start()
                logger.info("SportMonks scheduler started")
            
            # Keep the process running
            logger.info("Scheduler service is running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(60)  # Sleep for 1 minute
                    # Log heartbeat every hour
                    if datetime.now().minute == 0:
                        logger.info("Scheduler heartbeat - service is running")
            except KeyboardInterrupt:
                logger.info("Scheduler service stopped by user")
                if sportmonks_scheduler.scheduler.running:
                    sportmonks_scheduler.stop()
                sys.exit(0)
                
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    run_scheduler()