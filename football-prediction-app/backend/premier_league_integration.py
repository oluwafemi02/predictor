"""
Integration with Premier League data using web scraping
Based on the Premier League API repository
"""
import requests
from bs4 import BeautifulSoup
import re
from models import db, Team, Player, Match, TeamStatistics
from app import create_app
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PremierLeagueDataIntegration:
    """Class to handle Premier League data integration"""
    
    def __init__(self):
        self.base_url = "https://www.premierleague.com"
        self.onefootball_base = "https://onefootball.com"
    
    def fetch_league_table(self):
        """Fetch current league table from web scraping"""
        try:
            link = f"{self.onefootball_base}/en/competition/premier-league-9/table"
            response = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'})
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch league table: {response.status_code}")
                return []
            
            page = BeautifulSoup(response.text, "html.parser")
            rows = page.find_all("li", class_="Standing_standings__row__5sdZG")
            
            table_data = []
            for row in rows:
                try:
                    position_elem = row.find("div", class_="Standing_standings__cell__5Kd0W")
                    team_elem = row.find("p", class_="Standing_standings__teamName__psv61")
                    stats = row.find_all("div", class_="Standing_standings__cell__5Kd0W")
                    
                    if position_elem and team_elem and len(stats) >= 8:
                        team_name = team_elem.text.strip()
                        table_data.append({
                            "position": int(position_elem.text.strip()),
                            "team": team_name,
                            "played": int(stats[2].text.strip()),
                            "wins": int(stats[3].text.strip()),
                            "draws": int(stats[4].text.strip()),
                            "losses": int(stats[5].text.strip()),
                            "goal_difference": stats[6].text.strip(),
                            "points": int(stats[7].text.strip())
                        })
                except Exception as e:
                    logger.error(f"Error parsing row: {e}")
                    continue
            
            return table_data
        except Exception as e:
            logger.error(f"Error fetching league table: {e}")
            return []
    
    def fetch_fixtures(self, team_name=None):
        """Fetch fixtures from web scraping"""
        try:
            link = f"{self.onefootball_base}/en/competition/premier-league-9/fixtures"
            response = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'})
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch fixtures: {response.status_code}")
                return []
            
            page = BeautifulSoup(response.text, "html.parser")
            fixtures = page.find_all("a", class_="MatchCard_matchCard__iOv4G")
            
            fixtures_list = []
            for fixture in fixtures:
                fixture_text = fixture.get_text(separator=" ")
                if team_name and team_name not in fixture_text:
                    continue
                fixtures_list.append(fixture_text)
            
            return fixtures_list
        except Exception as e:
            logger.error(f"Error fetching fixtures: {e}")
            return []
    
    def update_team_statistics(self):
        """Update team statistics in the database from web scraping"""
        table_data = self.fetch_league_table()
        
        if not table_data:
            logger.warning("No table data fetched")
            return False
        
        updated_count = 0
        for data in table_data:
            # Find team by name (fuzzy matching)
            team = Team.query.filter(
                Team.name.ilike(f"%{data['team']}%")
            ).first()
            
            if not team:
                # Try alternative matching
                team_name_parts = data['team'].split()
                for part in team_name_parts:
                    if len(part) > 3:  # Skip short words
                        team = Team.query.filter(
                            Team.name.ilike(f"%{part}%")
                        ).first()
                        if team:
                            break
            
            if team:
                # Update or create team statistics
                stats = TeamStatistics.query.filter_by(
                    team_id=team.id,
                    season="2024/25"
                ).first()
                
                if not stats:
                    stats = TeamStatistics(
                        team_id=team.id,
                        season="2024/25",
                        competition="Premier League"
                    )
                    db.session.add(stats)
                
                # Parse goal difference
                gd_parts = data["goal_difference"].split(":")
                goals_for = int(gd_parts[0]) if len(gd_parts) > 0 and gd_parts[0].isdigit() else 0
                goals_against = int(gd_parts[1]) if len(gd_parts) > 1 and gd_parts[1].isdigit() else 0
                
                # Update statistics
                stats.matches_played = data["played"]
                stats.wins = data["wins"]
                stats.draws = data["draws"]
                stats.losses = data["losses"]
                stats.goals_for = goals_for
                stats.goals_against = goals_against
                
                # Update form (last 5 matches - simplified)
                if stats.wins > 0:
                    form_chars = []
                    recent_wins = min(stats.wins, 3)
                    recent_draws = min(stats.draws, 1)
                    recent_losses = min(stats.losses, 1)
                    
                    form_chars.extend(['W'] * recent_wins)
                    form_chars.extend(['D'] * recent_draws)
                    form_chars.extend(['L'] * recent_losses)
                    
                    stats.form = ''.join(form_chars[:5]).ljust(5, 'N')
                else:
                    stats.form = "NNNNN"
                
                updated_count += 1
                logger.info(f"Updated statistics for {team.name}")
            else:
                logger.warning(f"Could not find team: {data['team']}")
        
        db.session.commit()
        logger.info(f"Updated statistics for {updated_count} teams")
        return True
    
    def search_player_info(self, player_name):
        """Search for player information (simplified version)"""
        try:
            # For now, return mock data since we need Google search API
            # In production, this would use the googlesearch-python library
            return {
                "name": player_name,
                "position": "Unknown",
                "club": "Unknown",
                "nationality": "Unknown",
                "stats": {
                    "appearances": 0,
                    "goals": 0,
                    "assists": 0
                }
            }
        except Exception as e:
            logger.error(f"Error searching player info: {e}")
            return None

def integrate_premier_league_data():
    """Main function to integrate Premier League data"""
    app = create_app()
    
    with app.app_context():
        integration = PremierLeagueDataIntegration()
        
        print("Integrating Premier League data...")
        
        # Update team statistics
        print("Updating team statistics from live data...")
        if integration.update_team_statistics():
            print("✓ Team statistics updated successfully")
        else:
            print("✗ Failed to update team statistics")
        
        # Fetch fixtures
        print("\nFetching upcoming fixtures...")
        fixtures = integration.fetch_fixtures()
        if fixtures:
            print(f"✓ Found {len(fixtures)} upcoming fixtures")
            print("Sample fixtures:")
            for fixture in fixtures[:5]:
                print(f"  - {fixture}")
        else:
            print("✗ No fixtures found")
        
        print("\nIntegration completed!")

if __name__ == "__main__":
    integrate_premier_league_data()