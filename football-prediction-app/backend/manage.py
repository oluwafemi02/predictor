#!/usr/bin/env python
"""
Management script for Football Prediction App
Provides commands to manually trigger scheduled tasks
"""
import click
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from scheduler import DataScheduler

@click.group()
def cli():
    """Football Prediction App management commands"""
    pass

@cli.command()
@click.option('--env', default='development', help='Environment to run in')
def fetch_historical(env):
    """Fetch historical match data from past seasons"""
    app = create_app(env)
    scheduler = DataScheduler(app)
    
    with app.app_context():
        click.echo("Starting historical data fetch...")
        scheduler.fetch_historical_data()
        click.echo("Historical data fetch completed!")

@cli.command()
@click.option('--env', default='development', help='Environment to run in')
def fetch_upcoming(env):
    """Fetch upcoming match data"""
    app = create_app(env)
    scheduler = DataScheduler(app)
    
    with app.app_context():
        click.echo("Starting upcoming matches fetch...")
        scheduler.fetch_upcoming_matches()
        click.echo("Upcoming matches fetch completed!")

@cli.command()
@click.option('--env', default='development', help='Environment to run in')
def update_results(env):
    """Update match results for recent matches"""
    app = create_app(env)
    scheduler = DataScheduler(app)
    
    with app.app_context():
        click.echo("Updating match results...")
        scheduler.update_match_results()
        click.echo("Match results update completed!")

@cli.command()
@click.option('--env', default='development', help='Environment to run in')
def train_model(env):
    """Train the prediction model"""
    app = create_app(env)
    scheduler = DataScheduler(app)
    
    with app.app_context():
        click.echo("Starting model training...")
        scheduler.train_model()
        click.echo("Model training completed!")

@cli.command()
@click.option('--env', default='development', help='Environment to run in')
def run_scheduler(env):
    """Run the scheduler (keeps running until interrupted)"""
    app = create_app(env)
    
    # Enable scheduler
    app.config['ENABLE_SCHEDULER'] = True
    
    from scheduler import data_scheduler
    data_scheduler.init_app(app)
    data_scheduler.start()
    
    click.echo("Scheduler started. Press Ctrl+C to stop.")
    
    try:
        # Keep the script running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        data_scheduler.shutdown()
        click.echo("\nScheduler stopped.")

if __name__ == '__main__':
    cli()