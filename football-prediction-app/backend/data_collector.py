import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from models import db, Team, Player, Match, TeamStatistics, Injury, PlayerPerformance, HeadToHead, MatchOdds
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

# RapidAPI Football Odds Collector
class RapidAPIFootballOddsCollector:
    def __init__(self):
        self.api_key = Config.RAPIDAPI_KEY
        self.api_host = Config.RAPIDAPI_HOST
        self.base_url = Config.RAPIDAPI_ODDS_BASE_URL
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': self.api_host
        }
    
    def fetch_leagues(self) -> List[Dict]:
        """Fetch available leagues with odds"""
        try:
            response = requests.get(
                f"{self.base_url}/leagues",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get('api', {}).get('leagues', [])
        except Exception as e:
            logger.error(f"Error fetching leagues: {str(e)}")
            return []
    
    def fetch_bookmakers(self) -> List[Dict]:
        """Fetch available bookmakers"""
        try:
            response = requests.get(
                f"{self.base_url}/bookmakers",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get('api', {}).get('bookmakers', [])
        except Exception as e:
            logger.error(f"Error fetching bookmakers: {str(e)}")
            return []
    
    def fetch_odds_by_league(self, league_id: int, bookmaker_id: int = 5, page: int = 1) -> Dict:
        """Fetch odds for a specific league and bookmaker"""
        try:
            response = requests.get(
                f"{self.base_url}/league/{league_id}/bookmaker/{bookmaker_id}",
                headers=self.headers,
                params={'page': page}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching odds for league {league_id}: {str(e)}")
            return {}
    
    def fetch_odds_by_fixture(self, fixture_id: int) -> Dict:
        """Fetch odds for a specific fixture from all bookmakers"""
        try:
            response = requests.get(
                f"{self.base_url}/fixture/{fixture_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching odds for fixture {fixture_id}: {str(e)}")
            return {}
    
    def fetch_odds_by_date(self, date: str) -> Dict:
        """Fetch odds for all fixtures on a specific date (YYYY-MM-DD)"""
        try:
            response = requests.get(
                f"{self.base_url}/date/{date}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching odds for date {date}: {str(e)}")
            return {}
    
    def parse_odds_data(self, odds_data: Dict) -> Dict:
        """Parse odds data from API response into a structured format"""
        parsed_odds = {
            'match_winner': {},
            'over_under_2_5': {},
            'btts': {},
            'asian_handicap': {},
            'other': {}
        }
        
        for bet_type in odds_data:
            bet_label = bet_type.get('labelName', '')
            values = bet_type.get('values', [])
            
            if bet_label == 'Match Winner':
                for value in values:
                    if value.get('value') == 'Home':
                        parsed_odds['match_winner']['home'] = float(value.get('odd', 0))
                    elif value.get('value') == 'Draw':
                        parsed_odds['match_winner']['draw'] = float(value.get('odd', 0))
                    elif value.get('value') == 'Away':
                        parsed_odds['match_winner']['away'] = float(value.get('odd', 0))
            
            elif bet_label == 'Goals Over/Under' and '2.5' in str(values):
                for value in values:
                    if 'Over' in value.get('value', ''):
                        parsed_odds['over_under_2_5']['over'] = float(value.get('odd', 0))
                    elif 'Under' in value.get('value', ''):
                        parsed_odds['over_under_2_5']['under'] = float(value.get('odd', 0))
            
            elif bet_label == 'Both Teams Score':
                for value in values:
                    if value.get('value') == 'Yes':
                        parsed_odds['btts']['yes'] = float(value.get('odd', 0))
                    elif value.get('value') == 'No':
                        parsed_odds['btts']['no'] = float(value.get('odd', 0))
            
            elif 'Asian Handicap' in bet_label:
                parsed_odds['asian_handicap'][bet_label] = values
            
            else:
                parsed_odds['other'][bet_label] = values
        
        return parsed_odds
    
    def sync_odds_for_match(self, match: Match, fixture_id: int):
        """Sync odds data for a specific match"""
        odds_response = self.fetch_odds_by_fixture(fixture_id)
        
        if not odds_response or 'api' not in odds_response:
            logger.warning(f"No odds data found for fixture {fixture_id}")
            return
        
        odds_data = odds_response['api'].get('odds', [])
        
        for bookmaker_odds in odds_data:
            bookmaker = bookmaker_odds.get('bookmakers', [{}])[0]
            if not bookmaker:
                continue
            
            bookmaker_id = bookmaker.get('bookmaker_id')
            bookmaker_name = bookmaker.get('bookmaker_name')
            bets = bookmaker.get('bets', [])
            
            if not bets:
                continue
            
            # Parse odds data
            parsed_odds = self.parse_odds_data(bets)
            
            # Check if odds already exist for this match and bookmaker
            match_odds = MatchOdds.query.filter_by(
                match_id=match.id,
                bookmaker_id=bookmaker_id
            ).first()
            
            if not match_odds:
                match_odds = MatchOdds(
                    match_id=match.id,
                    fixture_id=fixture_id,
                    bookmaker_id=bookmaker_id,
                    bookmaker_name=bookmaker_name
                )
                db.session.add(match_odds)
            
            # Update odds values
            match_odds.home_win_odds = parsed_odds['match_winner'].get('home')
            match_odds.draw_odds = parsed_odds['match_winner'].get('draw')
            match_odds.away_win_odds = parsed_odds['match_winner'].get('away')
            
            match_odds.over_2_5_odds = parsed_odds['over_under_2_5'].get('over')
            match_odds.under_2_5_odds = parsed_odds['over_under_2_5'].get('under')
            
            match_odds.btts_yes_odds = parsed_odds['btts'].get('yes')
            match_odds.btts_no_odds = parsed_odds['btts'].get('no')
            
            # Store additional odds in JSON
            match_odds.additional_odds = {
                'asian_handicap': parsed_odds['asian_handicap'],
                'other': parsed_odds['other']
            }
            
            match_odds.update_timestamp = datetime.utcnow()
        
        db.session.commit()
        logger.info(f"Updated odds for match {match.id} (fixture {fixture_id})")
    
    def sync_league_odds(self, league_id: int, bookmaker_id: int = 5, max_pages: int = 5):
        """Sync odds for all matches in a league"""
        for page in range(1, max_pages + 1):
            odds_response = self.fetch_odds_by_league(league_id, bookmaker_id, page)
            
            if not odds_response or 'api' not in odds_response:
                break
            
            odds_data = odds_response['api'].get('odds', [])
            if not odds_data:
                break
            
            for fixture_odds in odds_data:
                fixture = fixture_odds.get('fixture', {})
                fixture_id = fixture.get('fixture_id')
                
                if not fixture_id:
                    continue
                
                # Try to find matching match in database
                # This is a simplified matching - you might need more sophisticated logic
                home_team_name = fixture.get('homeTeam', {}).get('team_name')
                away_team_name = fixture.get('awayTeam', {}).get('team_name')
                
                if not home_team_name or not away_team_name:
                    continue
                
                # Find teams
                home_team = Team.query.filter_by(name=home_team_name).first()
                away_team = Team.query.filter_by(name=away_team_name).first()
                
                if not home_team or not away_team:
                    logger.warning(f"Teams not found: {home_team_name} vs {away_team_name}")
                    continue
                
                # Find match
                match_date = datetime.fromisoformat(fixture.get('event_timestamp', '').replace('Z', '+00:00'))
                match = Match.query.filter_by(
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    match_date=match_date
                ).first()
                
                if match:
                    self.sync_odds_for_match(match, fixture_id)
                else:
                    logger.warning(f"Match not found for fixture {fixture_id}")
            
            logger.info(f"Processed page {page} of league {league_id} odds")
            
            # Check if there are more pages
            if len(odds_data) < 10:  # Assuming 10 results per page
                break