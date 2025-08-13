"""
Script to populate sample player data
"""
from models import db, Player, Team
from app import create_app
from datetime import datetime
import random

# Sample player data for each team
SAMPLE_PLAYERS = {
    "GK": ["Goalkeeper"],
    "DEF": ["Left Back", "Center Back", "Right Back", "Defender"],
    "MID": ["Defensive Midfielder", "Central Midfielder", "Attacking Midfielder", "Midfielder"],
    "FWD": ["Striker", "Winger", "Forward"]
}

NATIONALITIES = ["England", "Brazil", "France", "Spain", "Germany", "Argentina", "Portugal", "Italy", "Netherlands", "Belgium"]

def generate_player_name():
    """Generate a random player name"""
    first_names = ["James", "Mohamed", "Marcus", "Bruno", "Kevin", "Harry", "Raheem", "Jack", "Mason", "Phil",
                   "Bukayo", "Martin", "Gabriel", "Declan", "Trent", "Jordan", "Luke", "Ben", "Reece", "Kai"]
    last_names = ["Silva", "Kane", "Sterling", "Mount", "Rice", "Shaw", "Pickford", "Grealish", "Foden", "Saka",
                  "Alexander-Arnold", "Henderson", "Walker", "Chilwell", "Rashford", "Sancho", "Bellingham", "Martinez", "Jesus", "Fernandes"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def populate_players():
    """Populate sample players for each team"""
    app = create_app()
    
    with app.app_context():
        teams = Team.query.all()
        
        if not teams:
            print("No teams found. Please run populate_data.py first.")
            return
        
        players_created = 0
        
        for team in teams:
            # Check if team already has players
            existing_players = Player.query.filter_by(team_id=team.id).count()
            if existing_players > 0:
                print(f"Team {team.name} already has players, skipping...")
                continue
            
            # Create squad (typical 25 players)
            jersey_number = 1
            
            # Goalkeepers (3)
            for i in range(3):
                player = Player(
                    name=generate_player_name(),
                    position="GK",
                    team_id=team.id,
                    jersey_number=jersey_number,
                    age=random.randint(20, 35),
                    nationality=random.choice(NATIONALITIES),
                    height=random.randint(180, 200) / 100.0  # Height in meters
                )
                db.session.add(player)
                jersey_number += 1
                players_created += 1
            
            # Defenders (8)
            for i in range(8):
                player = Player(
                    name=generate_player_name(),
                    position="DEF",
                    team_id=team.id,
                    jersey_number=jersey_number,
                    age=random.randint(20, 35),
                    nationality=random.choice(NATIONALITIES),
                    height=random.randint(175, 195) / 100.0  # Height in meters
                )
                db.session.add(player)
                jersey_number += 1
                players_created += 1
            
            # Midfielders (8)
            for i in range(8):
                player = Player(
                    name=generate_player_name(),
                    position="MID",
                    team_id=team.id,
                    jersey_number=jersey_number,
                    age=random.randint(20, 35),
                    nationality=random.choice(NATIONALITIES),
                    height=random.randint(170, 190) / 100.0  # Height in meters
                )
                db.session.add(player)
                jersey_number += 1
                players_created += 1
            
            # Forwards (6)
            for i in range(6):
                player = Player(
                    name=generate_player_name(),
                    position="FWD",
                    team_id=team.id,
                    jersey_number=jersey_number,
                    age=random.randint(20, 35),
                    nationality=random.choice(NATIONALITIES),
                    height=random.randint(170, 190) / 100.0  # Height in meters
                )
                db.session.add(player)
                jersey_number += 1
                players_created += 1
            
            print(f"Created 25 players for {team.name}")
        
        db.session.commit()
        print(f"\nTotal players created: {players_created}")
        
        # Verify
        total_players = Player.query.count()
        print(f"Total players in database: {total_players}")

if __name__ == "__main__":
    populate_players()