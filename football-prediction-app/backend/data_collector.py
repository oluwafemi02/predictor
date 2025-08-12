import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from models import db, Team, Player, Match, TeamStatistics, Injury, PlayerPerformance, HeadToHead
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FootballDataCollector:
    def __init__(self):
        self.api_key = Config.FOOTBALL_API_KEY
        self.base_url = Config.FOOTBALL_API_BASE_URL
        self.headers = {
            'X-Auth-Token': self.api_key
        }
    
    def fetch_competitions(self) -> List[Dict]:
        """Fetch available competitions"""
        try:
            response = requests.get(f"{self.base_url}competitions", headers=self.headers)
            response.raise_for_status()
            return response.json().get('competitions', [])
        except Exception as e:
            logger.error(f"Error fetching competitions: {str(e)}")
            return []
    
    def fetch_teams(self, competition_id: int) -> List[Dict]:
        """Fetch teams for a specific competition"""
        try:
            response = requests.get(
                f"{self.base_url}competitions/{competition_id}/teams",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get('teams', [])
        except Exception as e:
            logger.error(f"Error fetching teams: {str(e)}")
            return []
    
    def fetch_matches(self, competition_id: int, date_from: str = None, date_to: str = None) -> List[Dict]:
        """Fetch matches for a specific competition"""
        params = {}
        if date_from:
            params['dateFrom'] = date_from
        if date_to:
            params['dateTo'] = date_to
        
        try:
            response = requests.get(
                f"{self.base_url}competitions/{competition_id}/matches",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json().get('matches', [])
        except Exception as e:
            logger.error(f"Error fetching matches: {str(e)}")
            return []
    
    def fetch_team_details(self, team_id: int) -> Dict:
        """Fetch detailed information about a team"""
        try:
            response = requests.get(
                f"{self.base_url}teams/{team_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching team details: {str(e)}")
            return {}
    
    def fetch_player_details(self, player_id: int) -> Dict:
        """Fetch detailed information about a player"""
        try:
            response = requests.get(
                f"{self.base_url}persons/{player_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching player details: {str(e)}")
            return {}
    
    def sync_teams(self, competition_id: int):
        """Sync teams from API to database"""
        teams_data = self.fetch_teams(competition_id)
        
        for team_data in teams_data:
            team = Team.query.filter_by(name=team_data['name']).first()
            if not team:
                team = Team(
                    name=team_data['name'],
                    code=team_data.get('tla'),
                    logo_url=team_data.get('crest'),
                    stadium=team_data.get('venue'),
                    founded=team_data.get('founded')
                )
                db.session.add(team)
        
        db.session.commit()
        logger.info(f"Synced {len(teams_data)} teams")
    
    def sync_matches(self, competition_id: int, season: str = None):
        """Sync matches from API to database"""
        # Get matches from last 30 days to next 30 days
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        date_to = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        matches_data = self.fetch_matches(competition_id, date_from, date_to)
        
        for match_data in matches_data:
            # Find teams
            home_team = Team.query.filter_by(name=match_data['homeTeam']['name']).first()
            away_team = Team.query.filter_by(name=match_data['awayTeam']['name']).first()
            
            if not home_team or not away_team:
                continue
            
            # Check if match exists
            match_date = datetime.fromisoformat(match_data['utcDate'].replace('Z', '+00:00'))
            match = Match.query.filter_by(
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                match_date=match_date
            ).first()
            
            if not match:
                match = Match(
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    match_date=match_date,
                    venue=match_data.get('venue'),
                    competition=match_data['competition']['name'],
                    season=season or match_data.get('season', {}).get('id'),
                    round=match_data.get('matchday'),
                    status=match_data['status'].lower()
                )
                db.session.add(match)
            else:
                # Update match status and scores
                match.status = match_data['status'].lower()
                if match_data['status'] == 'FINISHED':
                    match.home_score = match_data['score']['fullTime']['home']
                    match.away_score = match_data['score']['fullTime']['away']
                    match.home_score_halftime = match_data['score']['halfTime']['home']
                    match.away_score_halftime = match_data['score']['halfTime']['away']
        
        db.session.commit()
        logger.info(f"Synced {len(matches_data)} matches")
    
    def calculate_team_statistics(self, team_id: int, season: str):
        """Calculate and update team statistics"""
        team = Team.query.get(team_id)
        if not team:
            return
        
        # Get all matches for the team in the season
        matches = Match.query.filter(
            db.or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.season == season,
            Match.status == 'finished'
        ).all()
        
        stats = TeamStatistics.query.filter_by(team_id=team_id, season=season).first()
        if not stats:
            stats = TeamStatistics(team_id=team_id, season=season)
            db.session.add(stats)
        
        # Reset statistics
        stats.matches_played = len(matches)
        stats.wins = 0
        stats.draws = 0
        stats.losses = 0
        stats.goals_for = 0
        stats.goals_against = 0
        stats.clean_sheets = 0
        stats.home_wins = 0
        stats.home_draws = 0
        stats.home_losses = 0
        stats.away_wins = 0
        stats.away_draws = 0
        stats.away_losses = 0
        
        # Calculate statistics
        form_results = []
        for match in matches[-5:]:  # Last 5 matches for form
            is_home = match.home_team_id == team_id
            
            if is_home:
                team_score = match.home_score
                opponent_score = match.away_score
            else:
                team_score = match.away_score
                opponent_score = match.home_score
            
            stats.goals_for += team_score
            stats.goals_against += opponent_score
            
            if opponent_score == 0:
                stats.clean_sheets += 1
            
            if team_score > opponent_score:
                stats.wins += 1
                form_results.append('W')
                if is_home:
                    stats.home_wins += 1
                else:
                    stats.away_wins += 1
            elif team_score == opponent_score:
                stats.draws += 1
                form_results.append('D')
                if is_home:
                    stats.home_draws += 1
                else:
                    stats.away_draws += 1
            else:
                stats.losses += 1
                form_results.append('L')
                if is_home:
                    stats.home_losses += 1
                else:
                    stats.away_losses += 1
        
        stats.form = ''.join(form_results)
        db.session.commit()
        logger.info(f"Updated statistics for {team.name}")
    
    def update_head_to_head(self, team1_id: int, team2_id: int):
        """Update head-to-head statistics between two teams"""
        # Ensure team1_id < team2_id for consistency
        if team1_id > team2_id:
            team1_id, team2_id = team2_id, team1_id
        
        h2h = HeadToHead.query.filter_by(team1_id=team1_id, team2_id=team2_id).first()
        if not h2h:
            h2h = HeadToHead(team1_id=team1_id, team2_id=team2_id)
            db.session.add(h2h)
        
        # Get all matches between these teams
        matches = Match.query.filter(
            db.or_(
                db.and_(Match.home_team_id == team1_id, Match.away_team_id == team2_id),
                db.and_(Match.home_team_id == team2_id, Match.away_team_id == team1_id)
            ),
            Match.status == 'finished'
        ).order_by(Match.match_date.desc()).all()
        
        h2h.total_matches = len(matches)
        h2h.team1_wins = 0
        h2h.draws = 0
        h2h.team2_wins = 0
        h2h.team1_goals = 0
        h2h.team2_goals = 0
        
        last_5_results = []
        
        for i, match in enumerate(matches):
            if match.home_team_id == team1_id:
                team1_score = match.home_score
                team2_score = match.away_score
            else:
                team1_score = match.away_score
                team2_score = match.home_score
            
            h2h.team1_goals += team1_score
            h2h.team2_goals += team2_score
            
            if team1_score > team2_score:
                h2h.team1_wins += 1
                result = 'W1'
            elif team2_score > team1_score:
                h2h.team2_wins += 1
                result = 'W2'
            else:
                h2h.draws += 1
                result = 'D'
            
            if i < 5:  # Last 5 matches
                last_5_results.append({
                    'date': match.match_date.isoformat(),
                    'result': result,
                    'score': f"{team1_score}-{team2_score}"
                })
        
        h2h.last_5_results = last_5_results
        db.session.commit()
        logger.info(f"Updated head-to-head statistics")

# Alternative data collector using a free API (TheSportsDB)
class FreeSportsDataCollector:
    def __init__(self):
        self.base_url = "https://www.thesportsdb.com/api/v1/json/3"
    
    def fetch_leagues(self) -> List[Dict]:
        """Fetch available football leagues"""
        try:
            response = requests.get(f"{self.base_url}/all_leagues.php")
            response.raise_for_status()
            data = response.json()
            # Filter for soccer/football leagues
            return [league for league in data.get('leagues', []) if league.get('strSport') == 'Soccer']
        except Exception as e:
            logger.error(f"Error fetching leagues: {str(e)}")
            return []
    
    def fetch_teams_by_league(self, league_id: int) -> List[Dict]:
        """Fetch teams in a specific league"""
        try:
            response = requests.get(f"{self.base_url}/lookup_all_teams.php?id={league_id}")
            response.raise_for_status()
            return response.json().get('teams', [])
        except Exception as e:
            logger.error(f"Error fetching teams: {str(e)}")
            return []
    
    def fetch_past_matches(self, league_id: int, season: str) -> List[Dict]:
        """Fetch past matches for a league and season"""
        try:
            response = requests.get(f"{self.base_url}/eventsseason.php?id={league_id}&s={season}")
            response.raise_for_status()
            return response.json().get('events', [])
        except Exception as e:
            logger.error(f"Error fetching past matches: {str(e)}")
            return []
    
    def fetch_next_matches(self, league_id: int) -> List[Dict]:
        """Fetch upcoming matches for a league"""
        try:
            response = requests.get(f"{self.base_url}/eventsnextleague.php?id={league_id}")
            response.raise_for_status()
            return response.json().get('events', [])
        except Exception as e:
            logger.error(f"Error fetching next matches: {str(e)}")
            return []