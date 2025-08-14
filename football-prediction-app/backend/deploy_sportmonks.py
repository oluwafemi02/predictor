#!/usr/bin/env python
"""
SportMonks Deployment Helper Script
Run this after deploying to Render to initialize SportMonks data
"""

import sys
import time
from app import create_app
from models import db
from sportmonks_scheduler import sportmonks_scheduler
from sportmonks_client import SportMonksAPIClient

def main():
    print("🚀 SportMonks Deployment Helper")
    print("=" * 50)
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Step 1: Test database connection
        print("\n1. Testing database connection...")
        try:
            db.engine.execute("SELECT 1")
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            sys.exit(1)
        
        # Step 2: Create SportMonks tables
        print("\n2. Creating SportMonks tables...")
        try:
            from sportmonks_models import (
                SportMonksLeague, SportMonksTeam, SportMonksFixture,
                SportMonksPrediction, SportMonksValueBet, SportMonksOdds,
                SportMonksLiveData, SportMonksPlayer, SportMonksStanding
            )
            db.create_all()
            print("✅ SportMonks tables created successfully")
        except Exception as e:
            print(f"❌ Failed to create tables: {str(e)}")
            sys.exit(1)
        
        # Step 3: Test SportMonks API
        print("\n3. Testing SportMonks API connection...")
        try:
            client = SportMonksAPIClient()
            health = client.health_check()
            if health['api_status'] == 'healthy':
                print(f"✅ SportMonks API is healthy")
                print(f"   - Rate limit remaining: {health['rate_limit_remaining']}")
                print(f"   - Cache enabled: {health['cache_enabled']}")
            else:
                print("⚠️  SportMonks API health check failed")
        except Exception as e:
            print(f"❌ Failed to connect to SportMonks API: {str(e)}")
            sys.exit(1)
        
        # Step 4: Initialize scheduler
        print("\n4. Initializing SportMonks scheduler...")
        try:
            sportmonks_scheduler.init_app(app)
            print("✅ Scheduler initialized")
            
            # Ask if user wants to run initial data sync
            response = input("\nDo you want to run initial data sync? This may take a few minutes. (y/n): ")
            if response.lower() == 'y':
                print("\nRunning initial data sync...")
                print("This will fetch:")
                print("  - Leagues and teams")
                print("  - Upcoming fixtures for the next 7 days")
                print("  - Predictions for upcoming matches")
                
                # Run initial updates
                print("\n🔄 Fetching leagues and teams...")
                sportmonks_scheduler.update_leagues_and_teams()
                
                print("\n🔄 Fetching upcoming fixtures...")
                sportmonks_scheduler.update_upcoming_fixtures()
                
                print("\n🔄 Fetching predictions...")
                sportmonks_scheduler.update_predictions()
                
                print("\n✅ Initial data sync completed!")
            else:
                print("\nSkipping initial data sync. The scheduler will start syncing data automatically.")
        except Exception as e:
            print(f"❌ Failed to initialize scheduler: {str(e)}")
            sys.exit(1)
        
        # Step 5: Summary
        print("\n" + "=" * 50)
        print("🎉 SportMonks deployment completed successfully!")
        print("\nNext steps:")
        print("1. Visit your frontend URL and navigate to /sportmonks")
        print("2. Check the scheduler logs to ensure it's running")
        print("3. Monitor the API health endpoint: /api/sportmonks/health")
        print("\nEnjoy your SportMonks-powered football prediction app! ⚽")

if __name__ == "__main__":
    main()