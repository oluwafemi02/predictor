"""
Script to populate the database with Premier League data
"""
import requests
from bs4 import BeautifulSoup
from models import db, Team, Match, TeamStatistics
from app import create_app
from datetime import datetime
import json

# Premier League teams data
PREMIER_LEAGUE_TEAMS = [
    {"id": 1, "name": "Arsenal", "code": "ARS", "stadium": "Emirates Stadium", "founded": 1886},
    {"id": 2, "name": "Aston Villa", "code": "AVL", "stadium": "Villa Park", "founded": 1874},
    {"id": 3, "name": "Bournemouth", "code": "BOU", "stadium": "Vitality Stadium", "founded": 1899},
    {"id": 4, "name": "Brentford", "code": "BRE", "stadium": "Brentford Community Stadium", "founded": 1889},
    {"id": 5, "name": "Brighton & Hove Albion", "code": "BHA", "stadium": "American Express Stadium", "founded": 1901},
    {"id": 6, "name": "Burnley", "code": "BUR", "stadium": "Turf Moor", "founded": 1882},
    {"id": 7, "name": "Chelsea", "code": "CHE", "stadium": "Stamford Bridge", "founded": 1905},
    {"id": 8, "name": "Crystal Palace", "code": "CRY", "stadium": "Selhurst Park", "founded": 1905},
    {"id": 9, "name": "Everton", "code": "EVE", "stadium": "Goodison Park", "founded": 1878},
    {"id": 10, "name": "Fulham", "code": "FUL", "stadium": "Craven Cottage", "founded": 1879},
    {"id": 11, "name": "Liverpool", "code": "LIV", "stadium": "Anfield", "founded": 1892},
    {"id": 12, "name": "Luton Town", "code": "LUT", "stadium": "Kenilworth Road", "founded": 1885},
    {"id": 13, "name": "Manchester City", "code": "MCI", "stadium": "Etihad Stadium", "founded": 1880},
    {"id": 14, "name": "Manchester United", "code": "MUN", "stadium": "Old Trafford", "founded": 1878},
    {"id": 15, "name": "Newcastle United", "code": "NEW", "stadium": "St James' Park", "founded": 1892},
    {"id": 16, "name": "Nottingham Forest", "code": "NFO", "stadium": "City Ground", "founded": 1865},
    {"id": 17, "name": "Sheffield United", "code": "SHU", "stadium": "Bramall Lane", "founded": 1889},
    {"id": 18, "name": "Tottenham Hotspur", "code": "TOT", "stadium": "Tottenham Hotspur Stadium", "founded": 1882},
    {"id": 19, "name": "West Ham United", "code": "WHU", "stadium": "London Stadium", "founded": 1895},
    {"id": 20, "name": "Wolverhampton Wanderers", "code": "WOL", "stadium": "Molineux Stadium", "founded": 1877}
]

def fetch_league_table():
    """Fetch current league table data from web scraping"""
    try:
        # Using the same approach as the Premier League API
        link = "https://onefootball.com/en/competition/premier-league-9/table"
        response = requests.get(link)
        if response.status_code != 200:
            print(f"Failed to fetch league table: {response.status_code}")
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
                print(f"Error parsing row: {e}")
                continue
        
        return table_data
    except Exception as e:
        print(f"Error fetching league table: {e}")
        return []

def populate_teams():
    """Populate teams in the database"""
    for team_data in PREMIER_LEAGUE_TEAMS:
        existing_team = Team.query.filter_by(id=team_data["id"]).first()
        if not existing_team:
            team = Team(
                id=team_data["id"],
                name=team_data["name"],
                code=team_data["code"],
                stadium=team_data["stadium"],
                founded=team_data["founded"],
                logo_url=f"https://resources.premierleague.com/premierleague/badges/t{team_data['id']}.svg"
            )
            db.session.add(team)
    
    db.session.commit()
    print(f"Added {len(PREMIER_LEAGUE_TEAMS)} teams to the database")

def populate_team_statistics():
    """Populate team statistics from league table"""
    table_data = fetch_league_table()
    
    if not table_data:
        print("No table data fetched, creating sample data...")
        # Create sample data for demonstration
        for team in Team.query.all():
            stats = TeamStatistics(
                team_id=team.id,
                season="2023/24",
                matches_played=38,
                wins=20 - (team.id % 10),
                draws=10 - (team.id % 5),
                losses=8 + (team.id % 5),
                goals_for=70 - (team.id * 2),
                goals_against=30 + (team.id),
                clean_sheets=15 - (team.id % 8),
                form="WWLDW"[:5]
            )
            db.session.add(stats)
    else:
        # Use real data from web scraping
        for data in table_data:
            # Find team by name (fuzzy matching)
            team = None
            for t in Team.query.all():
                if data["team"].lower() in t.name.lower() or t.name.lower() in data["team"].lower():
                    team = t
                    break
            
            if team:
                # Check if statistics already exist
                existing_stats = TeamStatistics.query.filter_by(
                    team_id=team.id,
                    season="2023/24"
                ).first()
                
                if not existing_stats:
                    gd_parts = data["goal_difference"].split(":")
                    goals_for = int(gd_parts[0]) if len(gd_parts) > 0 else 0
                    goals_against = int(gd_parts[1]) if len(gd_parts) > 1 else 0
                    
                    stats = TeamStatistics(
                        team_id=team.id,
                        season="2023/24",
                        matches_played=data["played"],
                        wins=data["wins"],
                        draws=data["draws"],
                        losses=data["losses"],
                        goals_for=goals_for,
                        goals_against=goals_against,
                        clean_sheets=data["wins"] // 2,  # Approximate
                        form="WWLDW"  # Default form
                    )
                    db.session.add(stats)
    
    db.session.commit()
    print("Team statistics populated")

def populate_sample_matches():
    """Populate sample matches for demonstration"""
    teams = Team.query.all()
    if len(teams) < 2:
        print("Not enough teams to create matches")
        return
    
    # Create some recent matches
    match_date = datetime(2024, 3, 1)
    matches_created = 0
    
    for i in range(0, min(len(teams), 10), 2):
        match = Match(
            home_team_id=teams[i].id,
            away_team_id=teams[i+1].id,
            match_date=match_date,
            competition="Premier League",
            season="2023/24",
            round="Matchday 30",
            home_score=2,
            away_score=1,
            status="finished"
        )
        db.session.add(match)
        matches_created += 1
        
        # Create upcoming match
        upcoming_match = Match(
            home_team_id=teams[i+1].id,
            away_team_id=teams[i].id,
            match_date=datetime(2024, 12, 20),
            competition="Premier League",
            season="2024/25",
            round="Matchday 17",
            status="scheduled"
        )
        db.session.add(upcoming_match)
        matches_created += 1
    
    db.session.commit()
    print(f"Created {matches_created} sample matches")

def main():
    """Main function to populate the database"""
    app = create_app()
    
    with app.app_context():
        print("Starting database population...")
        
        # Populate teams
        populate_teams()
        
        # Populate team statistics
        populate_team_statistics()
        
        # Populate sample matches
        populate_sample_matches()
        
        print("Database population completed!")
        
        # Verify data
        teams_count = Team.query.count()
        matches_count = Match.query.count()
        stats_count = TeamStatistics.query.count()
        
        print(f"\nDatabase summary:")
        print(f"  Teams: {teams_count}")
        print(f"  Matches: {matches_count}")
        print(f"  Team Statistics: {stats_count}")

if __name__ == "__main__":
    main()