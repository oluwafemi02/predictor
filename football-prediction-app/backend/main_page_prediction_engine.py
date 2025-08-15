"""
Main Page Prediction Engine
Enhanced AI-powered prediction system with comprehensive data aggregation
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class TeamFormData:
    """Comprehensive team form data"""
    team_id: int
    team_name: str
    last_10_results: List[Dict] = field(default_factory=list)  # Full match details
    home_form: List[str] = field(default_factory=list)  # W/D/L for home matches
    away_form: List[str] = field(default_factory=list)  # W/D/L for away matches
    goals_scored_last_5: int = 0
    goals_conceded_last_5: int = 0
    clean_sheets_last_5: int = 0
    btts_last_5: int = 0
    form_rating: float = 0.0  # 0-10 scale
    current_streak: str = ""  # e.g., "W3" for 3 wins in a row
    avg_goals_scored: float = 0.0
    avg_goals_conceded: float = 0.0

@dataclass
class H2HData:
    """Head-to-head comprehensive data"""
    total_matches: int = 0
    home_wins: int = 0
    away_wins: int = 0
    draws: int = 0
    last_5_meetings: List[Dict] = field(default_factory=list)
    avg_total_goals: float = 0.0
    btts_percentage: float = 0.0
    over_25_percentage: float = 0.0
    home_team_avg_scored: float = 0.0
    away_team_avg_scored: float = 0.0
    dominant_team: Optional[str] = None
    
@dataclass
class InjurySuspensionData:
    """Injury and suspension report"""
    team_id: int
    team_name: str
    injuries: List[Dict] = field(default_factory=list)
    suspensions: List[Dict] = field(default_factory=list)
    key_players_missing: List[str] = field(default_factory=list)
    impact_score: float = 0.0  # 0-10 (10 = severe impact)
    top_scorer_available: bool = True
    first_choice_gk_available: bool = True
    defensive_crisis: bool = False

@dataclass
class StandingsData:
    """League standings and motivation data"""
    team_id: int
    position: int
    points: int
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    form_last_5: str  # e.g., "WWLDW"
    points_from_top: int
    points_from_relegation: int
    in_title_race: bool
    in_relegation_battle: bool
    in_european_race: bool
    motivation_level: float  # 0-10

@dataclass
class LiveContextData:
    """Live scores and context for match day"""
    other_results_impact: List[Dict] = field(default_factory=list)
    weather_conditions: Optional[Dict] = None
    referee_stats: Optional[Dict] = None
    travel_distance: Optional[float] = None
    days_since_last_match: int = 0
    upcoming_important_match: Optional[Dict] = None

@dataclass
class MainPagePrediction:
    """Enhanced prediction output for main page"""
    fixture_id: int
    home_team: str
    away_team: str
    date: str
    # Main predictions
    win_probability_home: float
    win_probability_away: float
    draw_probability: float
    # Additional predictions
    btts_probability: float
    over_25_probability: float
    under_25_probability: float
    over_35_probability: float
    # Confidence and summary
    confidence_level: str  # "high", "medium", "low"
    confidence_score: float  # 0-100
    prediction_summary: str
    # Detailed breakdown
    correct_score_predictions: List[Dict] = field(default_factory=list)
    factors_breakdown: Dict = field(default_factory=dict)
    data_completeness: float = 0.0  # Percentage of data available
    value_bets: List[Dict] = field(default_factory=list)

class MainPagePredictionEngine:
    """
    Comprehensive prediction engine for the main page
    Aggregates all available data sources for maximum accuracy
    """
    
    # Refined weights based on data importance
    WEIGHTS = {
        'recent_form': 0.40,        # 40% - Recent team form & goals
        'head_to_head': 0.20,       # 20% - Head-to-head history
        'injuries': 0.15,           # 15% - Injuries/suspensions impact
        'home_away': 0.10,          # 10% - Home/away advantage
        'motivation': 0.10,         # 10% - League standing & motivation
        'context': 0.05             # 5% - Other context (weather, referee, etc.)
    }
    
    def __init__(self, sportmonks_client):
        self.client = sportmonks_client
        self.executor = ThreadPoolExecutor(max_workers=15)
        
    def generate_comprehensive_prediction(self, fixture_id: int) -> Optional[MainPagePrediction]:
        """
        Generate comprehensive prediction by aggregating all data sources
        """
        try:
            logger.info(f"Generating comprehensive prediction for fixture {fixture_id}")
            
            # Fetch fixture details first
            fixture_data = self._fetch_fixture_details(fixture_id)
            if not fixture_data:
                logger.error(f"Could not fetch fixture details for {fixture_id}")
                return None
                
            home_team_id = fixture_data['home_team_id']
            away_team_id = fixture_data['away_team_id']
            
            # Parallel data fetching for all sources
            futures = {
                'home_form': self.executor.submit(self._fetch_team_form, home_team_id, is_home=True),
                'away_form': self.executor.submit(self._fetch_team_form, away_team_id, is_home=False),
                'h2h': self.executor.submit(self._fetch_h2h_data, home_team_id, away_team_id),
                'home_injuries': self.executor.submit(self._fetch_injury_data, home_team_id),
                'away_injuries': self.executor.submit(self._fetch_injury_data, away_team_id),
                'home_standings': self.executor.submit(self._fetch_standings_data, home_team_id, fixture_data['league_id']),
                'away_standings': self.executor.submit(self._fetch_standings_data, away_team_id, fixture_data['league_id']),
                'sportmonks_pred': self.executor.submit(self._fetch_sportmonks_predictions, fixture_id),
                'live_context': self.executor.submit(self._fetch_live_context, fixture_data)
            }
            
            # Collect results
            results = {}
            data_completeness = 0
            total_sources = len(futures)
            
            for key, future in futures.items():
                try:
                    results[key] = future.result(timeout=10)
                    if results[key] is not None:
                        data_completeness += 1
                except Exception as e:
                    logger.warning(f"Failed to fetch {key}: {str(e)}")
                    results[key] = None
                    
            data_completeness = (data_completeness / total_sources) * 100
            
            # Calculate predictions based on available data
            prediction = self._calculate_weighted_prediction(
                fixture_data=fixture_data,
                home_form=results.get('home_form'),
                away_form=results.get('away_form'),
                h2h_data=results.get('h2h'),
                home_injuries=results.get('home_injuries'),
                away_injuries=results.get('away_injuries'),
                home_standings=results.get('home_standings'),
                away_standings=results.get('away_standings'),
                sportmonks_pred=results.get('sportmonks_pred'),
                live_context=results.get('live_context')
            )
            
            prediction.data_completeness = data_completeness
            
            # Generate human-readable summary
            prediction.prediction_summary = self._generate_prediction_summary(prediction, results)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error generating prediction for fixture {fixture_id}: {str(e)}")
            return None
            
    def _fetch_fixture_details(self, fixture_id: int) -> Optional[Dict]:
        """Fetch comprehensive fixture details"""
        try:
            response = self.client.get_fixture_with_predictions(fixture_id)
            if not response or 'data' not in response:
                return None
                
            fixture = response['data']
            participants = fixture.get('participants', [])
            home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
            away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
            
            return {
                'fixture_id': fixture_id,
                'home_team_id': home_team.get('id'),
                'away_team_id': away_team.get('id'),
                'home_team_name': home_team.get('name', 'Unknown'),
                'away_team_name': away_team.get('name', 'Unknown'),
                'date': fixture.get('starting_at'),
                'league_id': fixture.get('league_id'),
                'venue_id': fixture.get('venue_id'),
                'state': fixture.get('state', {})
            }
        except Exception as e:
            logger.error(f"Error fetching fixture details: {str(e)}")
            return None
            
    def _fetch_team_form(self, team_id: int, is_home: bool) -> Optional[TeamFormData]:
        """Fetch comprehensive team form data"""
        try:
            # Get recent fixtures
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            
            response = self.client.get_fixtures_between_dates_for_team(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
                team_id,
                include=['participants', 'scores', 'league', 'events']
            )
            
            if not response or 'data' not in response:
                return None
                
            fixtures = sorted(response['data'], key=lambda x: x['starting_at'], reverse=True)[:10]
            
            form_data = TeamFormData(team_id=team_id, team_name="")
            
            # Analyze last 10 matches
            for i, fixture in enumerate(fixtures):
                participants = fixture.get('participants', [])
                team = next((p for p in participants if p['id'] == team_id), None)
                if not team:
                    continue
                    
                is_home_match = team.get('meta', {}).get('location') == 'home'
                scores = fixture.get('scores', [])
                
                # Get final score
                final_score = next((s for s in scores if s.get('description') == 'CURRENT'), None)
                if not final_score:
                    continue
                    
                home_score = final_score.get('score', {}).get('participant', {}).get('home', 0)
                away_score = final_score.get('score', {}).get('participant', {}).get('away', 0)
                
                # Determine result
                if is_home_match:
                    team_score = home_score
                    opponent_score = away_score
                else:
                    team_score = away_score
                    opponent_score = home_score
                    
                if team_score > opponent_score:
                    result = 'W'
                elif team_score < opponent_score:
                    result = 'L'
                else:
                    result = 'D'
                    
                # Store match details
                form_data.last_10_results.append({
                    'date': fixture['starting_at'],
                    'result': result,
                    'goals_for': team_score,
                    'goals_against': opponent_score,
                    'is_home': is_home_match
                })
                
                # Update form arrays
                if i < 5:  # Last 5 matches
                    form_data.goals_scored_last_5 += team_score
                    form_data.goals_conceded_last_5 += opponent_score
                    if opponent_score == 0:
                        form_data.clean_sheets_last_5 += 1
                    if team_score > 0 and opponent_score > 0:
                        form_data.btts_last_5 += 1
                        
                    if is_home_match:
                        form_data.home_form.append(result)
                    else:
                        form_data.away_form.append(result)
                        
            # Calculate ratings
            if form_data.last_10_results:
                total_matches = len(form_data.last_10_results)
                wins = sum(1 for r in form_data.last_10_results if r['result'] == 'W')
                draws = sum(1 for r in form_data.last_10_results if r['result'] == 'D')
                
                form_data.form_rating = (wins * 3 + draws) / (total_matches * 3) * 10
                form_data.avg_goals_scored = sum(r['goals_for'] for r in form_data.last_10_results) / total_matches
                form_data.avg_goals_conceded = sum(r['goals_against'] for r in form_data.last_10_results) / total_matches
                
                # Current streak
                streak_type = form_data.last_10_results[0]['result']
                streak_count = 1
                for r in form_data.last_10_results[1:]:
                    if r['result'] == streak_type:
                        streak_count += 1
                    else:
                        break
                form_data.current_streak = f"{streak_type}{streak_count}"
                
            return form_data
            
        except Exception as e:
            logger.error(f"Error fetching team form for {team_id}: {str(e)}")
            return None
            
    def _fetch_h2h_data(self, home_team_id: int, away_team_id: int) -> Optional[H2HData]:
        """Fetch head-to-head data between teams"""
        try:
            response = self.client.get_head_to_head(
                home_team_id, 
                away_team_id,
                include=['participants', 'scores', 'league', 'events']
            )
            
            if not response or 'data' not in response:
                return None
                
            h2h_data = H2HData()
            fixtures = response['data'][:10]  # Last 10 meetings
            
            total_goals = 0
            btts_count = 0
            over_25_count = 0
            
            for fixture in fixtures:
                participants = fixture.get('participants', [])
                home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), None)
                away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), None)
                
                if not home_team or not away_team:
                    continue
                    
                scores = fixture.get('scores', [])
                final_score = next((s for s in scores if s.get('description') == 'CURRENT'), None)
                
                if not final_score:
                    continue
                    
                home_goals = final_score.get('score', {}).get('participant', {}).get('home', 0)
                away_goals = final_score.get('score', {}).get('participant', {}).get('away', 0)
                
                # Track which team won
                home_is_current_home = home_team['id'] == home_team_id
                
                if home_goals > away_goals:
                    if home_is_current_home:
                        h2h_data.home_wins += 1
                    else:
                        h2h_data.away_wins += 1
                elif away_goals > home_goals:
                    if home_is_current_home:
                        h2h_data.away_wins += 1
                    else:
                        h2h_data.home_wins += 1
                else:
                    h2h_data.draws += 1
                    
                h2h_data.total_matches += 1
                total_goals += home_goals + away_goals
                
                if home_goals > 0 and away_goals > 0:
                    btts_count += 1
                if home_goals + away_goals > 2.5:
                    over_25_count += 1
                    
                # Store last 5 meetings
                if len(h2h_data.last_5_meetings) < 5:
                    h2h_data.last_5_meetings.append({
                        'date': fixture['starting_at'],
                        'home_team': home_team['name'],
                        'away_team': away_team['name'],
                        'score': f"{home_goals}-{away_goals}",
                        'total_goals': home_goals + away_goals
                    })
                    
            # Calculate statistics
            if h2h_data.total_matches > 0:
                h2h_data.avg_total_goals = total_goals / h2h_data.total_matches
                h2h_data.btts_percentage = (btts_count / h2h_data.total_matches) * 100
                h2h_data.over_25_percentage = (over_25_count / h2h_data.total_matches) * 100
                
                # Determine dominant team
                if h2h_data.home_wins > h2h_data.away_wins * 1.5:
                    h2h_data.dominant_team = "home"
                elif h2h_data.away_wins > h2h_data.home_wins * 1.5:
                    h2h_data.dominant_team = "away"
                else:
                    h2h_data.dominant_team = None
                    
            return h2h_data
            
        except Exception as e:
            logger.error(f"Error fetching H2H data: {str(e)}")
            return None
            
    def _fetch_injury_data(self, team_id: int) -> Optional[InjurySuspensionData]:
        """Fetch injury and suspension data for a team"""
        try:
            response = self.client.get_team_injuries(team_id, include=['player'])
            
            if not response or 'data' not in response:
                return None
                
            injury_data = InjurySuspensionData(team_id=team_id, team_name="")
            
            for injury in response['data']:
                player = injury.get('player', {})
                
                injury_info = {
                    'player_name': player.get('display_name', 'Unknown'),
                    'player_id': player.get('id'),
                    'position': player.get('position', {}).get('name', 'Unknown'),
                    'reason': injury.get('reason', 'Unknown'),
                    'return_date': injury.get('expected_return'),
                    'is_suspension': injury.get('category', '').lower() == 'suspension'
                }
                
                if injury_info['is_suspension']:
                    injury_data.suspensions.append(injury_info)
                else:
                    injury_data.injuries.append(injury_info)
                    
                # Check if key player
                if player.get('is_key_player') or player.get('market_value', 0) > 10000000:
                    injury_data.key_players_missing.append(injury_info['player_name'])
                    
                # Check position impact
                position = injury_info['position'].lower()
                if 'goalkeeper' in position:
                    injury_data.first_choice_gk_available = False
                elif 'defender' in position:
                    injury_data.defensive_crisis = True
                elif 'forward' in position or 'striker' in position:
                    injury_data.top_scorer_available = False
                    
            # Calculate impact score
            total_out = len(injury_data.injuries) + len(injury_data.suspensions)
            key_players_out = len(injury_data.key_players_missing)
            
            injury_data.impact_score = min(10, (total_out * 0.5 + key_players_out * 2))
            
            return injury_data
            
        except Exception as e:
            logger.error(f"Error fetching injury data for team {team_id}: {str(e)}")
            return None
            
    def _fetch_standings_data(self, team_id: int, league_id: int) -> Optional[StandingsData]:
        """Fetch current standings and motivation data"""
        try:
            # Get current season
            season_id = self.client.get_current_season_id(league_id)
            if not season_id:
                return None
                
            response = self.client.get_standings_by_season(season_id, include=['team'])
            
            if not response or 'data' not in response:
                return None
                
            standings = response['data']
            team_standing = None
            
            for standing in standings:
                if standing.get('team_id') == team_id:
                    team_standing = standing
                    break
                    
            if not team_standing:
                return None
                
            standings_data = StandingsData(
                team_id=team_id,
                position=team_standing.get('position', 0),
                points=team_standing.get('points', 0),
                played=team_standing.get('games_played', 0),
                won=team_standing.get('won', 0),
                drawn=team_standing.get('draw', 0),
                lost=team_standing.get('lost', 0),
                goals_for=team_standing.get('goals_scored', 0),
                goals_against=team_standing.get('goals_against', 0),
                goal_difference=team_standing.get('goal_difference', 0),
                form_last_5=team_standing.get('recent_form', '')
            )
            
            # Calculate motivation factors
            total_teams = len(standings)
            standings_data.points_from_top = standings[0]['points'] - standings_data.points
            
            # Find relegation zone (usually bottom 3)
            relegation_position = total_teams - 2
            if standings_data.position >= relegation_position:
                standings_data.points_from_relegation = 0
                standings_data.in_relegation_battle = True
            else:
                relegation_team = standings[relegation_position - 1]
                standings_data.points_from_relegation = standings_data.points - relegation_team['points']
                standings_data.in_relegation_battle = standings_data.points_from_relegation <= 6
                
            # Title race (within 9 points of top)
            standings_data.in_title_race = standings_data.points_from_top <= 9 and standings_data.position <= 4
            
            # European spots (usually top 6-7)
            standings_data.in_european_race = standings_data.position <= 8 and standings_data.position > 4
            
            # Calculate motivation level
            if standings_data.in_title_race:
                standings_data.motivation_level = 9.0
            elif standings_data.in_relegation_battle:
                standings_data.motivation_level = 9.5
            elif standings_data.in_european_race:
                standings_data.motivation_level = 8.0
            else:
                standings_data.motivation_level = 5.0  # Mid-table
                
            return standings_data
            
        except Exception as e:
            logger.error(f"Error fetching standings data: {str(e)}")
            return None
            
    def _fetch_sportmonks_predictions(self, fixture_id: int) -> Optional[Dict]:
        """Fetch SportMonks' own predictions"""
        try:
            response = self.client.get_fixture_with_predictions(fixture_id)
            
            if not response or 'data' not in response:
                return None
                
            predictions = response['data'].get('predictions', [])
            
            parsed_predictions = {
                'match_winner': None,
                'goals': {},
                'btts': None,
                'correct_scores': []
            }
            
            for pred in predictions:
                pred_type = pred.get('type', {}).get('code', '')
                pred_data = pred.get('predictions', {})
                
                if pred_type == 'fulltime-result-probability':
                    parsed_predictions['match_winner'] = {
                        'home': pred_data.get('home', 0),
                        'draw': pred_data.get('draw', 0),
                        'away': pred_data.get('away', 0)
                    }
                elif pred_type == 'both-teams-to-score-probability':
                    parsed_predictions['btts'] = {
                        'yes': pred_data.get('yes', 0),
                        'no': pred_data.get('no', 0)
                    }
                elif 'over-under' in pred_type:
                    if '2_5' in pred_type:
                        parsed_predictions['goals']['over_25'] = pred_data.get('yes', 0)
                        parsed_predictions['goals']['under_25'] = pred_data.get('no', 0)
                    elif '3_5' in pred_type:
                        parsed_predictions['goals']['over_35'] = pred_data.get('yes', 0)
                        parsed_predictions['goals']['under_35'] = pred_data.get('no', 0)
                elif pred_type == 'correct-score-probability':
                    scores = pred_data.get('scores', {})
                    for score, prob in scores.items():
                        if score not in ['Other_1', 'Other_2', 'Other_X'] and prob > 5:
                            parsed_predictions['correct_scores'].append({
                                'score': score,
                                'probability': prob
                            })
                            
            # Sort correct scores by probability
            parsed_predictions['correct_scores'].sort(key=lambda x: x['probability'], reverse=True)
            
            return parsed_predictions
            
        except Exception as e:
            logger.error(f"Error fetching SportMonks predictions: {str(e)}")
            return None
            
    def _fetch_live_context(self, fixture_data: Dict) -> Optional[LiveContextData]:
        """Fetch live context data for match day"""
        try:
            context = LiveContextData()
            
            # Get other matches on the same day that might affect motivation
            match_date = fixture_data['date'].split('T')[0]
            
            response = self.client.get_fixtures_between_dates(
                match_date, 
                match_date,
                include=['participants', 'scores', 'state']
            )
            
            if response and 'data' in response:
                # Find matches that could impact this fixture (same league, relegation rivals, etc.)
                relevant_matches = []
                for fixture in response['data']:
                    if fixture['id'] != fixture_data['fixture_id'] and fixture['league_id'] == fixture_data['league_id']:
                        relevant_matches.append({
                            'fixture_id': fixture['id'],
                            'teams': [p['name'] for p in fixture.get('participants', [])],
                            'time': fixture['starting_at'],
                            'state': fixture.get('state', {}).get('state', 'scheduled')
                        })
                        
                context.other_results_impact = relevant_matches[:5]  # Top 5 relevant matches
                
            return context
            
        except Exception as e:
            logger.error(f"Error fetching live context: {str(e)}")
            return None
            
    def _calculate_weighted_prediction(self, **kwargs) -> MainPagePrediction:
        """Calculate final prediction using weighted factors"""
        fixture_data = kwargs['fixture_data']
        
        # Initialize base prediction
        prediction = MainPagePrediction(
            fixture_id=fixture_data['fixture_id'],
            home_team=fixture_data['home_team_name'],
            away_team=fixture_data['away_team_name'],
            date=fixture_data['date'],
            win_probability_home=33.33,
            win_probability_away=33.33,
            draw_probability=33.34,
            btts_probability=50.0,
            over_25_probability=50.0,
            under_25_probability=50.0,
            over_35_probability=30.0,
            confidence_level="low",
            confidence_score=0.0,
            prediction_summary=""
        )
        
        factors_used = 0
        factors_breakdown = {}
        
        # 1. Recent Form Analysis (40%)
        home_form = kwargs.get('home_form')
        away_form = kwargs.get('away_form')
        
        if home_form and away_form:
            form_factor = self._analyze_form_factor(home_form, away_form)
            factors_breakdown['recent_form'] = form_factor
            
            # Apply form weight
            weight = self.WEIGHTS['recent_form']
            prediction.win_probability_home += form_factor['home_advantage'] * weight
            prediction.win_probability_away += form_factor['away_advantage'] * weight
            prediction.draw_probability += form_factor['draw_tendency'] * weight
            
            prediction.btts_probability = form_factor['btts_likelihood']
            prediction.over_25_probability = form_factor['over_25_likelihood']
            prediction.over_35_probability = form_factor['over_35_likelihood']
            
            factors_used += 1
            
        # 2. Head-to-Head Analysis (20%)
        h2h_data = kwargs.get('h2h_data')
        
        if h2h_data and h2h_data.total_matches >= 3:
            h2h_factor = self._analyze_h2h_factor(h2h_data)
            factors_breakdown['head_to_head'] = h2h_factor
            
            weight = self.WEIGHTS['head_to_head']
            prediction.win_probability_home += h2h_factor['home_historical_advantage'] * weight
            prediction.win_probability_away += h2h_factor['away_historical_advantage'] * weight
            prediction.draw_probability += h2h_factor['draw_historical_tendency'] * weight
            
            # Blend H2H patterns with form
            prediction.btts_probability = (prediction.btts_probability + h2h_data.btts_percentage) / 2
            prediction.over_25_probability = (prediction.over_25_probability + h2h_data.over_25_percentage) / 2
            
            factors_used += 1
            
        # 3. Injuries/Suspensions Impact (15%)
        home_injuries = kwargs.get('home_injuries')
        away_injuries = kwargs.get('away_injuries')
        
        if home_injuries and away_injuries:
            injury_factor = self._analyze_injury_factor(home_injuries, away_injuries)
            factors_breakdown['injuries'] = injury_factor
            
            weight = self.WEIGHTS['injuries']
            prediction.win_probability_home += injury_factor['home_impact'] * weight
            prediction.win_probability_away += injury_factor['away_impact'] * weight
            
            factors_used += 1
            
        # 4. Home/Away Advantage (10%)
        home_away_factor = self._analyze_home_away_factor(home_form, away_form)
        factors_breakdown['home_away'] = home_away_factor
        
        weight = self.WEIGHTS['home_away']
        prediction.win_probability_home += home_away_factor['home_boost'] * weight
        prediction.win_probability_away += home_away_factor['away_penalty'] * weight
        
        # 5. Motivation/League Standing (10%)
        home_standings = kwargs.get('home_standings')
        away_standings = kwargs.get('away_standings')
        
        if home_standings and away_standings:
            motivation_factor = self._analyze_motivation_factor(home_standings, away_standings)
            factors_breakdown['motivation'] = motivation_factor
            
            weight = self.WEIGHTS['motivation']
            prediction.win_probability_home += motivation_factor['home_motivation_boost'] * weight
            prediction.win_probability_away += motivation_factor['away_motivation_boost'] * weight
            
            factors_used += 1
            
        # 6. Blend with SportMonks predictions if available
        sportmonks_pred = kwargs.get('sportmonks_pred')
        if sportmonks_pred and sportmonks_pred.get('match_winner'):
            sm_weight = 0.3  # Give 30% weight to SportMonks predictions
            
            current_weight = 1 - sm_weight
            prediction.win_probability_home = (prediction.win_probability_home * current_weight + 
                                              sportmonks_pred['match_winner']['home'] * sm_weight)
            prediction.win_probability_away = (prediction.win_probability_away * current_weight + 
                                              sportmonks_pred['match_winner']['away'] * sm_weight)
            prediction.draw_probability = (prediction.draw_probability * current_weight + 
                                          sportmonks_pred['match_winner']['draw'] * sm_weight)
            
            if sportmonks_pred.get('goals'):
                prediction.over_25_probability = (prediction.over_25_probability * current_weight + 
                                                 sportmonks_pred['goals'].get('over_25', 50) * sm_weight)
                prediction.over_35_probability = (prediction.over_35_probability * current_weight + 
                                                 sportmonks_pred['goals'].get('over_35', 30) * sm_weight)
                
            if sportmonks_pred.get('btts'):
                prediction.btts_probability = (prediction.btts_probability * current_weight + 
                                              sportmonks_pred['btts']['yes'] * sm_weight)
                
            # Add correct scores
            prediction.correct_score_predictions = sportmonks_pred.get('correct_scores', [])[:5]
            
        # Normalize probabilities to sum to 100
        total_prob = prediction.win_probability_home + prediction.win_probability_away + prediction.draw_probability
        if total_prob > 0:
            prediction.win_probability_home = (prediction.win_probability_home / total_prob) * 100
            prediction.win_probability_away = (prediction.win_probability_away / total_prob) * 100
            prediction.draw_probability = (prediction.draw_probability / total_prob) * 100
            
        # Calculate under probabilities
        prediction.under_25_probability = 100 - prediction.over_25_probability
        
        # Determine confidence level
        max_prob = max(prediction.win_probability_home, prediction.win_probability_away, prediction.draw_probability)
        if max_prob >= 55 and factors_used >= 4:
            prediction.confidence_level = "high"
            prediction.confidence_score = 80 + (max_prob - 55) * 0.8
        elif max_prob >= 45 and factors_used >= 3:
            prediction.confidence_level = "medium"
            prediction.confidence_score = 60 + (max_prob - 45) * 2
        else:
            prediction.confidence_level = "low"
            prediction.confidence_score = 40 + (max_prob - 33) * 1.5
            
        prediction.factors_breakdown = factors_breakdown
        
        # Identify value bets
        prediction.value_bets = self._identify_value_bets(prediction)
        
        return prediction
        
    def _analyze_form_factor(self, home_form: TeamFormData, away_form: TeamFormData) -> Dict:
        """Analyze recent form to determine advantages"""
        factor = {
            'home_advantage': 0,
            'away_advantage': 0,
            'draw_tendency': 0,
            'btts_likelihood': 50,
            'over_25_likelihood': 50,
            'over_35_likelihood': 30
        }
        
        # Compare form ratings
        form_diff = home_form.form_rating - away_form.form_rating
        
        if form_diff > 2:
            factor['home_advantage'] = min(30, form_diff * 5)
        elif form_diff < -2:
            factor['away_advantage'] = min(30, abs(form_diff) * 5)
        else:
            factor['draw_tendency'] = 10 + abs(form_diff) * 2
            
        # Goal scoring patterns
        avg_home_goals = home_form.avg_goals_scored + away_form.avg_goals_conceded
        avg_away_goals = away_form.avg_goals_scored + home_form.avg_goals_conceded
        total_expected_goals = (avg_home_goals + avg_away_goals) / 2
        
        # BTTS probability
        home_scores_rate = (home_form.goals_scored_last_5 / 5) * 100
        away_scores_rate = (away_form.goals_scored_last_5 / 5) * 100
        factor['btts_likelihood'] = (home_scores_rate * away_scores_rate) / 100
        
        # Over/Under probabilities
        if total_expected_goals > 2.8:
            factor['over_25_likelihood'] = min(85, 50 + (total_expected_goals - 2.5) * 20)
            factor['over_35_likelihood'] = min(70, 30 + (total_expected_goals - 3.5) * 25)
        else:
            factor['over_25_likelihood'] = max(15, 50 - (2.5 - total_expected_goals) * 20)
            factor['over_35_likelihood'] = max(10, 30 - (3.5 - total_expected_goals) * 25)
            
        return factor
        
    def _analyze_h2h_factor(self, h2h_data: H2HData) -> Dict:
        """Analyze head-to-head history"""
        factor = {
            'home_historical_advantage': 0,
            'away_historical_advantage': 0,
            'draw_historical_tendency': 0
        }
        
        total = h2h_data.total_matches
        if total == 0:
            return factor
            
        # Calculate percentages
        home_win_pct = (h2h_data.home_wins / total) * 100
        away_win_pct = (h2h_data.away_wins / total) * 100
        draw_pct = (h2h_data.draws / total) * 100
        
        # Apply historical tendency with diminishing returns
        factor['home_historical_advantage'] = home_win_pct - 33.33
        factor['away_historical_advantage'] = away_win_pct - 33.33
        factor['draw_historical_tendency'] = draw_pct - 33.34
        
        # Check recent trend in last 5 meetings
        if h2h_data.last_5_meetings:
            recent_home_wins = sum(1 for m in h2h_data.last_5_meetings[:3] 
                                  if int(m['score'].split('-')[0]) > int(m['score'].split('-')[1]))
            if recent_home_wins >= 2:
                factor['home_historical_advantage'] *= 1.2
            elif recent_home_wins == 0:
                factor['away_historical_advantage'] *= 1.2
                
        return factor
        
    def _analyze_injury_factor(self, home_injuries: InjurySuspensionData, 
                              away_injuries: InjurySuspensionData) -> Dict:
        """Analyze injury impact on match outcome"""
        factor = {
            'home_impact': 0,
            'away_impact': 0
        }
        
        # Compare injury impacts
        injury_diff = away_injuries.impact_score - home_injuries.impact_score
        
        # Positive injury_diff means away team is more affected
        if injury_diff > 0:
            factor['home_impact'] = min(20, injury_diff * 3)
        else:
            factor['away_impact'] = min(20, abs(injury_diff) * 3)
            
        # Additional penalties for key positions
        if not home_injuries.top_scorer_available:
            factor['home_impact'] -= 5
        if not away_injuries.top_scorer_available:
            factor['away_impact'] -= 5
            
        if home_injuries.defensive_crisis:
            factor['home_impact'] -= 8
        if away_injuries.defensive_crisis:
            factor['away_impact'] -= 8
            
        return factor
        
    def _analyze_home_away_factor(self, home_form: Optional[TeamFormData], 
                                  away_form: Optional[TeamFormData]) -> Dict:
        """Analyze home/away advantage"""
        factor = {
            'home_boost': 15,  # Base home advantage
            'away_penalty': -5   # Base away disadvantage
        }
        
        # Adjust based on actual home/away form if available
        if home_form and home_form.home_form:
            home_wins = sum(1 for r in home_form.home_form if r == 'W')
            if home_wins >= 4:  # Strong home form
                factor['home_boost'] = 20
            elif home_wins <= 1:  # Poor home form
                factor['home_boost'] = 10
                
        if away_form and away_form.away_form:
            away_wins = sum(1 for r in away_form.away_form if r == 'W')
            if away_wins >= 3:  # Good away form
                factor['away_penalty'] = 0
            elif away_wins == 0:  # Poor away form
                factor['away_penalty'] = -10
                
        return factor
        
    def _analyze_motivation_factor(self, home_standings: StandingsData, 
                                   away_standings: StandingsData) -> Dict:
        """Analyze motivation based on league position"""
        factor = {
            'home_motivation_boost': 0,
            'away_motivation_boost': 0
        }
        
        # Compare motivation levels
        motivation_diff = home_standings.motivation_level - away_standings.motivation_level
        
        if motivation_diff > 1:
            factor['home_motivation_boost'] = min(15, motivation_diff * 3)
        elif motivation_diff < -1:
            factor['away_motivation_boost'] = min(15, abs(motivation_diff) * 3)
            
        # Special scenarios
        if home_standings.in_relegation_battle and not away_standings.in_relegation_battle:
            factor['home_motivation_boost'] += 5
        if away_standings.in_relegation_battle and not home_standings.in_relegation_battle:
            factor['away_motivation_boost'] += 5
            
        # Title race
        if home_standings.in_title_race and away_standings.position > 10:
            factor['home_motivation_boost'] += 3
        if away_standings.in_title_race and home_standings.position > 10:
            factor['away_motivation_boost'] += 3
            
        return factor
        
    def _identify_value_bets(self, prediction: MainPagePrediction) -> List[Dict]:
        """Identify potential value bets based on prediction confidence"""
        value_bets = []
        
        # Check for strong home/away predictions
        if prediction.win_probability_home >= 60 and prediction.confidence_level in ["high", "medium"]:
            value_bets.append({
                'type': 'Home Win',
                'probability': prediction.win_probability_home,
                'confidence': prediction.confidence_level,
                'recommended_stake': self._calculate_stake(prediction.win_probability_home)
            })
        elif prediction.win_probability_away >= 55 and prediction.confidence_level in ["high", "medium"]:
            value_bets.append({
                'type': 'Away Win',
                'probability': prediction.win_probability_away,
                'confidence': prediction.confidence_level,
                'recommended_stake': self._calculate_stake(prediction.win_probability_away)
            })
            
        # Over/Under bets
        if prediction.over_25_probability >= 70:
            value_bets.append({
                'type': 'Over 2.5 Goals',
                'probability': prediction.over_25_probability,
                'confidence': prediction.confidence_level,
                'recommended_stake': self._calculate_stake(prediction.over_25_probability)
            })
        elif prediction.under_25_probability >= 70:
            value_bets.append({
                'type': 'Under 2.5 Goals',
                'probability': prediction.under_25_probability,
                'confidence': prediction.confidence_level,
                'recommended_stake': self._calculate_stake(prediction.under_25_probability)
            })
            
        # BTTS
        if prediction.btts_probability >= 65 or prediction.btts_probability <= 35:
            bet_type = 'BTTS Yes' if prediction.btts_probability >= 65 else 'BTTS No'
            value_bets.append({
                'type': bet_type,
                'probability': prediction.btts_probability if bet_type == 'BTTS Yes' else 100 - prediction.btts_probability,
                'confidence': prediction.confidence_level,
                'recommended_stake': self._calculate_stake(max(prediction.btts_probability, 100 - prediction.btts_probability))
            })
            
        return value_bets
        
    def _calculate_stake(self, probability: float) -> float:
        """Calculate recommended stake based on Kelly Criterion (conservative)"""
        # Conservative Kelly: (probability - 50) / 50 * 0.25
        if probability <= 50:
            return 0.5  # Minimum stake
        edge = (probability - 50) / 50
        return min(3.0, 0.5 + edge * 2.5)  # Max 3 units
        
    def _generate_prediction_summary(self, prediction: MainPagePrediction, data_sources: Dict) -> str:
        """Generate human-readable prediction summary"""
        summary_parts = []
        
        # Main prediction
        if prediction.win_probability_home >= 55:
            summary_parts.append(f"{prediction.home_team} are strong favorites with {prediction.win_probability_home:.1f}% win probability")
        elif prediction.win_probability_away >= 50:
            summary_parts.append(f"{prediction.away_team} are slight favorites with {prediction.win_probability_away:.1f}% win probability")
        elif prediction.draw_probability >= 35:
            summary_parts.append(f"This match could end in a draw ({prediction.draw_probability:.1f}% probability)")
        else:
            summary_parts.append(f"Close match expected between {prediction.home_team} and {prediction.away_team}")
            
        # Form analysis
        home_form = data_sources.get('home_form')
        away_form = data_sources.get('away_form')
        if home_form and away_form:
            if home_form.form_rating > away_form.form_rating + 2:
                summary_parts.append(f"{prediction.home_team} are in excellent form ({home_form.current_streak})")
            elif away_form.form_rating > home_form.form_rating + 2:
                summary_parts.append(f"{prediction.away_team} are in better recent form ({away_form.current_streak})")
                
        # H2H insight
        h2h = data_sources.get('h2h')
        if h2h and h2h.dominant_team:
            team_name = prediction.home_team if h2h.dominant_team == "home" else prediction.away_team
            summary_parts.append(f"{team_name} have historically dominated this fixture")
            
        # Goal expectation
        if prediction.over_25_probability >= 65:
            summary_parts.append("Expect an entertaining match with over 2.5 goals likely")
        elif prediction.under_25_probability >= 65:
            summary_parts.append("This could be a low-scoring defensive battle")
            
        # Injuries impact
        home_injuries = data_sources.get('home_injuries')
        away_injuries = data_sources.get('away_injuries')
        if home_injuries and home_injuries.impact_score >= 7:
            summary_parts.append(f"{prediction.home_team} are severely affected by injuries")
        if away_injuries and away_injuries.impact_score >= 7:
            summary_parts.append(f"{prediction.away_team} have key players missing")
            
        # Motivation
        home_standings = data_sources.get('home_standings')
        away_standings = data_sources.get('away_standings')
        if home_standings and home_standings.in_relegation_battle:
            summary_parts.append(f"{prediction.home_team} desperately need points to avoid relegation")
        if away_standings and away_standings.in_title_race:
            summary_parts.append(f"{prediction.away_team} are fighting for the title")
            
        # Confidence note
        if prediction.confidence_level == "high":
            summary_parts.append(f"High confidence prediction based on {prediction.data_completeness:.0f}% data availability")
        elif prediction.confidence_level == "low":
            summary_parts.append("Lower confidence due to limited data or unpredictable factors")
            
        return ". ".join(summary_parts)
        
    def get_batch_predictions(self, fixture_ids: List[int], date_from: str, date_to: str) -> List[MainPagePrediction]:
        """Generate predictions for multiple fixtures efficiently"""
        predictions = []
        
        # Use thread pool for parallel processing
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_fixture = {
                executor.submit(self.generate_comprehensive_prediction, fixture_id): fixture_id
                for fixture_id in fixture_ids
            }
            
            for future in as_completed(future_to_fixture):
                fixture_id = future_to_fixture[future]
                try:
                    prediction = future.result()
                    if prediction:
                        predictions.append(prediction)
                except Exception as e:
                    logger.error(f"Failed to generate prediction for fixture {fixture_id}: {str(e)}")
                    
        return predictions