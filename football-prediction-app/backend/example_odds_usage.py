#!/usr/bin/env python3
"""
Example usage of the RapidAPI Football Odds Collector

This script demonstrates how to:
1. Fetch available leagues with odds
2. Fetch bookmakers
3. Get odds for a specific league
4. Sync odds with match data in the database
"""

from data_collector import RapidAPIFootballOddsCollector
from models import db, Match
from app import create_app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_usage():
    # Initialize the app context
    app = create_app()
    
    with app.app_context():
        # Create an instance of the odds collector
        odds_collector = RapidAPIFootballOddsCollector()
        
        # Example 1: Fetch available leagues
        print("\n=== Fetching Available Leagues ===")
        leagues = odds_collector.fetch_leagues()
        print(f"Found {len(leagues)} leagues with odds data")
        for league in leagues[:5]:  # Show first 5
            print(f"- {league.get('name')} (ID: {league.get('league_id')})")
        
        # Example 2: Fetch bookmakers
        print("\n=== Fetching Bookmakers ===")
        bookmakers = odds_collector.fetch_bookmakers()
        print(f"Found {len(bookmakers)} bookmakers")
        for bookmaker in bookmakers[:5]:  # Show first 5
            print(f"- {bookmaker.get('name')} (ID: {bookmaker.get('bookmaker_id')})")
        
        # Example 3: Fetch odds for a specific league (using the league ID from the URL you provided)
        print("\n=== Fetching Odds for League 865927 ===")
        league_id = 865927
        bookmaker_id = 5  # As specified in your URL
        page = 2  # As specified in your URL
        
        odds_data = odds_collector.fetch_odds_by_league(league_id, bookmaker_id, page)
        
        if odds_data and 'api' in odds_data:
            fixtures_with_odds = odds_data['api'].get('odds', [])
            print(f"Found odds for {len(fixtures_with_odds)} fixtures on page {page}")
            
            # Display first fixture odds as example
            if fixtures_with_odds:
                first_fixture = fixtures_with_odds[0]
                fixture_info = first_fixture.get('fixture', {})
                print(f"\nExample fixture: {fixture_info.get('homeTeam', {}).get('team_name')} vs {fixture_info.get('awayTeam', {}).get('team_name')}")
                print(f"Date: {fixture_info.get('event_date')}")
                
                # Show available bet types
                bookmaker_data = first_fixture.get('bookmakers', [{}])[0]
                if bookmaker_data:
                    bets = bookmaker_data.get('bets', [])
                    print(f"\nAvailable bet types from {bookmaker_data.get('bookmaker_name')}:")
                    for bet in bets[:5]:  # Show first 5 bet types
                        print(f"- {bet.get('label_name')}")
        
        # Example 4: Sync odds for matches in the database
        print("\n=== Syncing Odds with Database ===")
        # This would sync odds for all matches in the specified league
        # Uncomment the following line to actually sync (requires matches in database)
        # odds_collector.sync_league_odds(league_id, bookmaker_id, max_pages=1)
        
        # Example 5: Fetch odds by date
        print("\n=== Fetching Odds by Date ===")
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        odds_by_date = odds_collector.fetch_odds_by_date(today)
        
        if odds_by_date and 'api' in odds_by_date:
            fixtures_today = odds_by_date['api'].get('odds', [])
            print(f"Found odds for {len(fixtures_today)} fixtures on {today}")

def test_specific_fixture():
    """Test fetching odds for a specific fixture"""
    app = create_app()
    
    with app.app_context():
        odds_collector = RapidAPIFootballOddsCollector()
        
        # Example fixture ID (you would get this from the API or your database)
        fixture_id = 123456  # Replace with actual fixture ID
        
        print(f"\n=== Fetching Odds for Fixture {fixture_id} ===")
        odds_data = odds_collector.fetch_odds_by_fixture(fixture_id)
        
        if odds_data and 'api' in odds_data:
            all_bookmaker_odds = odds_data['api'].get('odds', [])
            print(f"Found odds from {len(all_bookmaker_odds)} bookmakers")
            
            # Parse and display odds
            for bookmaker_odds in all_bookmaker_odds[:3]:  # Show first 3 bookmakers
                bookmaker_info = bookmaker_odds.get('bookmakers', [{}])[0]
                if bookmaker_info:
                    print(f"\n{bookmaker_info.get('bookmaker_name')}:")
                    bets = bookmaker_info.get('bets', [])
                    parsed_odds = odds_collector.parse_odds_data(bets)
                    
                    # Display match winner odds
                    if parsed_odds['match_winner']:
                        print(f"  Match Winner - Home: {parsed_odds['match_winner'].get('home')}, "
                              f"Draw: {parsed_odds['match_winner'].get('draw')}, "
                              f"Away: {parsed_odds['match_winner'].get('away')}")
                    
                    # Display over/under 2.5 odds
                    if parsed_odds['over_under_2_5']:
                        print(f"  Over/Under 2.5 - Over: {parsed_odds['over_under_2_5'].get('over')}, "
                              f"Under: {parsed_odds['over_under_2_5'].get('under')}")

if __name__ == "__main__":
    print("RapidAPI Football Odds Collector Example")
    print("========================================")
    
    # Run the main example
    example_usage()
    
    # Uncomment to test specific fixture
    # test_specific_fixture()