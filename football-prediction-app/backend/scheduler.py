"""
Scheduler module for automated data extraction and model training
"""
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask
from models import db
from data_collector import FootballDataCollector
import requests
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataScheduler:
    def __init__(self, app: Flask = None):
        self.scheduler = BackgroundScheduler()
        self.app = app
        self.data_collector = FootballDataCollector()
        
    def init_app(self, app: Flask):
        """Initialize scheduler with Flask app context"""
        self.app = app
        
    def fetch_historical_data(self):
        """Fetch historical match data from past seasons"""
        with self.app.app_context():
            try:
                logger.info("Starting automated historical data fetch...")
                
                # Premier League ID for football-data.org
                competition_id = 2021
                
                # Fetch data for last 3 seasons
                current_year = datetime.now().year
                seasons = []
                
                # Determine seasons based on current month
                if datetime.now().month >= 8:  # August or later
                    # Current season has started
                    seasons = [
                        str(current_year),  # Current season
                        str(current_year - 1),  # Last season
                        str(current_year - 2)   # Two seasons ago
                    ]
                else:
                    # Current season hasn't started yet
                    seasons = [
                        str(current_year - 1),  # Last season
                        str(current_year - 2),  # Two seasons ago
                        str(current_year - 3)   # Three seasons ago
                    ]
                
                total_matches = 0
                for season in seasons:
                    try:
                        matches = self.data_collector.fetch_matches(
                            competition_id,
                            date_from=f"{season}-08-01",
                            date_to=f"{int(season) + 1}-05-31"
                        )
                        
                        if matches:
                            # Process and store matches
                            stored = self.data_collector.process_and_store_matches(matches)
                            total_matches += len(stored)
                            logger.info(f"Fetched {len(stored)} matches for season {season}/{int(season) + 1}")
                    
                    except Exception as e:
                        logger.error(f"Error fetching season {season}: {str(e)}")
                        continue
                
                logger.info(f"Historical data fetch completed. Total matches: {total_matches}")
                
                # Trigger model training if we have enough data
                if total_matches >= 50:
                    self.train_model()
                    
            except Exception as e:
                logger.error(f"Error in historical data fetch: {str(e)}")
    
    def fetch_upcoming_matches(self):
        """Fetch upcoming match data"""
        with self.app.app_context():
            try:
                logger.info("Starting automated upcoming matches fetch...")
                
                # Premier League ID
                competition_id = 2021
                
                # Fetch matches for next 30 days
                date_from = datetime.now().strftime('%Y-%m-%d')
                date_to = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                
                matches = self.data_collector.fetch_matches(
                    competition_id,
                    date_from=date_from,
                    date_to=date_to
                )
                
                if matches:
                    stored = self.data_collector.process_and_store_matches(matches)
                    logger.info(f"Fetched {len(stored)} upcoming matches")
                
                # Also update match results for recently finished matches
                self.update_match_results()
                
            except Exception as e:
                logger.error(f"Error in upcoming matches fetch: {str(e)}")
    
    def update_match_results(self):
        """Update results for recently finished matches"""
        with self.app.app_context():
            try:
                # Get matches from last 7 days that might have finished
                date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                date_to = datetime.now().strftime('%Y-%m-%d')
                
                competition_id = 2021
                matches = self.data_collector.fetch_matches(
                    competition_id,
                    date_from=date_from,
                    date_to=date_to
                )
                
                if matches:
                    updated = self.data_collector.update_match_results(matches)
                    logger.info(f"Updated results for {updated} matches")
                    
            except Exception as e:
                logger.error(f"Error updating match results: {str(e)}")
    
    def train_model(self):
        """Trigger model training via API"""
        with self.app.app_context():
            try:
                logger.info("Starting automated model training...")
                
                # Call the train model endpoint
                response = requests.post('http://localhost:5000/api/v1/model/train')
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Model training completed: {result}")
                else:
                    logger.error(f"Model training failed: {response.text}")
                    
            except Exception as e:
                logger.error(f"Error in model training: {str(e)}")
    
    def start(self):
        """Start the scheduler with configured jobs"""
        
        # Fetch historical data once on startup and then weekly
        self.scheduler.add_job(
            func=self.fetch_historical_data,
            trigger="interval",
            weeks=1,
            id='fetch_historical_data',
            name='Fetch historical match data',
            replace_existing=True
        )
        
        # Fetch upcoming matches twice daily (morning and evening)
        self.scheduler.add_job(
            func=self.fetch_upcoming_matches,
            trigger=CronTrigger(hour='9,18'),  # 9 AM and 6 PM
            id='fetch_upcoming_matches',
            name='Fetch upcoming matches',
            replace_existing=True
        )
        
        # Update match results every hour
        self.scheduler.add_job(
            func=self.update_match_results,
            trigger="interval",
            hours=1,
            id='update_match_results',
            name='Update match results',
            replace_existing=True
        )
        
        # Train model weekly on Sunday night
        self.scheduler.add_job(
            func=self.train_model,
            trigger=CronTrigger(day_of_week='sun', hour=23),
            id='train_model',
            name='Train prediction model',
            replace_existing=True
        )
        
        # Run initial data fetch after 10 seconds
        self.scheduler.add_job(
            func=self.fetch_historical_data,
            trigger="date",
            run_date=datetime.now() + timedelta(seconds=10),
            id='initial_fetch',
            name='Initial data fetch'
        )
        
        self.scheduler.start()
        logger.info("Scheduler started with all jobs configured")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")

# Global scheduler instance
data_scheduler = DataScheduler()