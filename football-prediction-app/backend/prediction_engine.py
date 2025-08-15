"""
Advanced Prediction Engine for Football Matches
Combines multiple data sources to generate AI-powered predictions
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
class TeamForm:
    """Recent form data for a team"""
    last_5_results: List[str] = field(default_factory=list)  # W/D/L
    last_5_goals_scored: List[int] = field(default_factory=list)
    last_5_goals_conceded: List[int] = field(default_factory=list)
    home_form: List[str] = field(default_factory=list)  # Last 5 home/away results
    away_form: List[str] = field(default_factory=list)
    goals_scored: int = 0
    goals_conceded: int = 0
    clean_sheets: int = 0
    btts_count: int = 0
    avg_goals_per_match: float = 0.0
    form_rating: float = 0.0  # 0-10 scale
    xg_for: float = 0.0  # Expected goals for
    xg_against: float = 0.0  # Expected goals against

@dataclass
class HeadToHeadStats:
    """Head-to-head statistics between two teams"""
    total_matches: int = 0
    home_wins: int = 0
    away_wins: int = 0
    draws: int = 0
    avg_goals_per_match: float = 0.0
    btts_percentage: float = 0.0
    over_25_percentage: float = 0.0
    recent_meetings: List[Dict] = field(default_factory=list)
    home_team_avg_goals: float = 0.0
    away_team_avg_goals: float = 0.0

@dataclass
class InjuryReport:
    """Injury and suspension data for a team"""
    key_players_out: List[Dict] = field(default_factory=list)
    total_injuries: int = 0
    impact_rating: float = 0.0  # 0-10 scale (10 = severe impact)
    missing_top_scorer: bool = False
    missing_goalkeeper: bool = False
    missing_key_defenders: int = 0

@dataclass
class TeamMotivation:
    """Motivation factors based on league position and objectives"""
    league_position: int = 0
    points_from_top: int = 0
    points_from_relegation: int = 0
    title_race: bool = False
    relegation_battle: bool = False
    european_spots_race: bool = False
    motivation_score: float = 5.0  # 0-10 scale
    games_remaining: int = 0
    recent_manager_change: bool = False

@dataclass
class AdvancedPrediction:
    """Complete enhanced prediction output"""
    fixture_id: int
    home_team: str
    away_team: str
    date: str
    win_probability_home: float
    win_probability_away: float
    draw_probability: float
    predicted_goals_home: float
    predicted_goals_away: float
    btts_probability: float
    over_25_probability: float
    over_35_probability: float
    under_25_probability: float
    confidence_score: float
    prediction_summary: str
    value_bets: List[Dict] = field(default_factory=list)
    data_sources: Dict = field(default_factory=dict)
    factors_breakdown: Dict = field(default_factory=dict)

class AdvancedPredictionEngine:
    """
    Advanced AI-powered prediction engine that combines multiple data sources
    """
    
    # Updated weights for different prediction factors (total = 100%)
    WEIGHTS = {
        'recent_form': 0.40,      # 40% - Recent team form & goals
        'head_to_head': 0.20,     # 20% - H2H history
        'injuries': 0.15,         # 15% - Injuries/suspensions impact
        'home_advantage': 0.10,   # 10% - Home/away advantage
        'motivation': 0.10,       # 10% - League standing & motivation
        'other_factors': 0.05     # 5% - Weather, travel, etc.
    }
    
    def __init__(self, sportmonks_client):
        self.client = sportmonks_client
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def generate_prediction(self, fixture_id: int) -> Optional[AdvancedPrediction]:
        """
        Generate enhanced prediction for a fixture by aggregating multiple data sources
        """
        try:
            # Get fixture details
            fixture_data = self._get_fixture_details(fixture_id)
            if not fixture_data:
                logger.error(f"Could not fetch fixture data for ID: {fixture_id}")
                return None
            
            # Extract team information
            participants = fixture_data.get('participants', [])
            home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), None)
            away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), None)
            
            if not home_team or not away_team:
                logger.error("Could not identify home and away teams")
                return None
            
            # Parallel data fetching
            future_to_data = {}
            
            with self.executor as executor:
                # Submit all data fetching tasks
                future_to_data[executor.submit(self._get_team_form, home_team['id'], True)] = 'home_form'
                future_to_data[executor.submit(self._get_team_form, away_team['id'], False)] = 'away_form'
                future_to_data[executor.submit(self._get_head_to_head_stats, home_team['id'], away_team['id'])] = 'h2h'
                future_to_data[executor.submit(self._get_injury_report, home_team['id'])] = 'home_injuries'
                future_to_data[executor.submit(self._get_injury_report, away_team['id'])] = 'away_injuries'
                future_to_data[executor.submit(self._get_team_motivation, home_team['id'], fixture_data.get('league_id'))] = 'home_motivation'
                future_to_data[executor.submit(self._get_team_motivation, away_team['id'], fixture_data.get('league_id'))] = 'away_motivation'
                future_to_data[executor.submit(self._get_sportmonks_prediction, fixture_id)] = 'base_prediction'
                
                # Collect results
                results = {}
                for future in as_completed(future_to_data):
                    key = future_to_data[future]
                    try:
                        results[key] = future.result()
                    except Exception as e:
                        logger.warning(f"Failed to fetch {key}: {str(e)}")
                        results[key] = None
            
            # Calculate prediction based on all factors
            prediction = self._calculate_prediction(
                fixture_data=fixture_data,
                home_team=home_team,
                away_team=away_team,
                home_form=results.get('home_form'),
                away_form=results.get('away_form'),
                h2h_stats=results.get('h2h'),
                home_injuries=results.get('home_injuries'),
                away_injuries=results.get('away_injuries'),
                home_motivation=results.get('home_motivation'),
                away_motivation=results.get('away_motivation'),
                base_prediction=results.get('base_prediction')
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error generating prediction for fixture {fixture_id}: {str(e)}")
            return None
    
    def _get_fixture_details(self, fixture_id: int) -> Optional[Dict]:
        """Get comprehensive fixture details"""
        result = self.client.get_fixture_with_predictions(fixture_id)
        if result and 'data' in result:
            return result['data']
        return None
    
    def _get_team_form(self, team_id: int, is_home: bool) -> TeamForm:
        """Get recent form data for a team"""
        try:
            # Get last 10 fixtures
            recent_fixtures = self.client.get_team_recent_fixtures(
                team_id, 
                limit=10,
                include=['participants', 'scores', 'statistics']
            )
            
            if not recent_fixtures or 'data' not in recent_fixtures:
                return TeamForm()
            
            form = TeamForm()
            fixtures = recent_fixtures['data'][:10]  # Last 10 matches
            
            for fixture in fixtures:
                # Determine if team was home or away
                participants = fixture.get('participants', [])
                team_location = None
                opponent = None
                
                for p in participants:
                    if p['id'] == team_id:
                        team_location = p.get('meta', {}).get('location')
                    else:
                        opponent = p
                
                if not team_location:
                    continue
                
                # Get scores
                scores = fixture.get('scores', [])
                ft_score = next((s for s in scores if s.get('description') == 'FULLTIME'), None)
                
                if ft_score:
                    team_goals = ft_score['score']['participant_home'] if team_location == 'home' else ft_score['score']['participant_away']
                    opponent_goals = ft_score['score']['participant_away'] if team_location == 'home' else ft_score['score']['participant_home']
                    
                    # Determine result
                    if team_goals > opponent_goals:
                        result = 'W'
                    elif team_goals < opponent_goals:
                        result = 'L'
                    else:
                        result = 'D'
                    
                    # Update form data
                    if len(form.last_5_results) < 5:
                        form.last_5_results.append(result)
                        form.last_5_goals_scored.append(team_goals)
                        form.last_5_goals_conceded.append(opponent_goals)
                    
                    # Update home/away specific form
                    if team_location == 'home' and len(form.home_form) < 5:
                        form.home_form.append(result)
                    elif team_location == 'away' and len(form.away_form) < 5:
                        form.away_form.append(result)
                    
                    # Update totals
                    form.goals_scored += team_goals
                    form.goals_conceded += opponent_goals
                    
                    if opponent_goals == 0:
                        form.clean_sheets += 1
                    
                    if team_goals > 0 and opponent_goals > 0:
                        form.btts_count += 1
            
            # Calculate averages and ratings
            matches_count = len(fixtures)
            if matches_count > 0:
                form.avg_goals_per_match = form.goals_scored / matches_count
                
                # Calculate form rating (0-10)
                points = sum(3 if r == 'W' else 1 if r == 'D' else 0 for r in form.last_5_results)
                form.form_rating = (points / 15.0) * 10  # Max 15 points from 5 games
            
            return form
            
        except Exception as e:
            logger.error(f"Error getting team form: {str(e)}")
            return TeamForm()
    
    def _get_head_to_head_stats(self, home_id: int, away_id: int) -> HeadToHeadStats:
        """Get head-to-head statistics between two teams"""
        try:
            h2h_data = self.client.get_head_to_head(
                home_id, 
                away_id,
                include=['participants', 'scores', 'state', 'venue']
            )
            
            if not h2h_data or 'data' not in h2h_data:
                return HeadToHeadStats()
            
            stats = HeadToHeadStats()
            fixtures = h2h_data['data'][:10]  # Last 10 H2H matches
            
            total_goals = 0
            
            for fixture in fixtures:
                participants = fixture.get('participants', [])
                home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), None)
                away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), None)
                
                if not home_team or not away_team:
                    continue
                
                # Get scores
                scores = fixture.get('scores', [])
                ft_score = next((s for s in scores if s.get('description') == 'FULLTIME'), None)
                
                if ft_score:
                    home_goals = ft_score['score']['participant_home']
                    away_goals = ft_score['score']['participant_away']
                    
                    stats.total_matches += 1
                    total_goals += home_goals + away_goals
                    
                    # Determine winner
                    if home_team['id'] == home_id:
                        if home_goals > away_goals:
                            stats.home_wins += 1
                        elif away_goals > home_goals:
                            stats.away_wins += 1
                        else:
                            stats.draws += 1
                        stats.home_team_avg_goals += home_goals
                        stats.away_team_avg_goals += away_goals
                    else:
                        if away_goals > home_goals:
                            stats.home_wins += 1
                        elif home_goals > away_goals:
                            stats.away_wins += 1
                        else:
                            stats.draws += 1
                        stats.home_team_avg_goals += away_goals
                        stats.away_team_avg_goals += home_goals
                    
                    # BTTS and Over 2.5
                    if home_goals > 0 and away_goals > 0:
                        stats.btts_percentage += 1
                    if home_goals + away_goals > 2.5:
                        stats.over_25_percentage += 1
                    
                    # Add to recent meetings
                    if len(stats.recent_meetings) < 5:
                        stats.recent_meetings.append({
                            'date': fixture.get('starting_at'),
                            'home_team': home_team.get('name'),
                            'away_team': away_team.get('name'),
                            'score': f"{home_goals}-{away_goals}",
                            'venue': fixture.get('venue', {}).get('name', 'Unknown')
                        })
            
            # Calculate percentages
            if stats.total_matches > 0:
                stats.avg_goals_per_match = total_goals / stats.total_matches
                stats.btts_percentage = (stats.btts_percentage / stats.total_matches) * 100
                stats.over_25_percentage = (stats.over_25_percentage / stats.total_matches) * 100
                stats.home_team_avg_goals /= stats.total_matches
                stats.away_team_avg_goals /= stats.total_matches
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting H2H stats: {str(e)}")
            return HeadToHeadStats()
    
    def _get_injury_report(self, team_id: int) -> InjuryReport:
        """Get injury and suspension report for a team"""
        try:
            injuries_data = self.client.get_team_injuries(team_id, include=['player'])
            
            if not injuries_data or 'data' not in injuries_data:
                return InjuryReport()
            
            report = InjuryReport()
            injuries = injuries_data['data']
            
            for injury in injuries:
                player = injury.get('player', {})
                
                # Determine player importance
                position = player.get('position', {}).get('name', '')
                is_key_player = False
                
                if 'Goalkeeper' in position:
                    report.missing_goalkeeper = True
                    is_key_player = True
                elif 'Defender' in position:
                    report.missing_key_defenders += 1
                    is_key_player = True
                elif 'Forward' in position or 'Striker' in position:
                    # Check if top scorer (simplified - would need more data)
                    is_key_player = True
                
                report.total_injuries += 1
                
                if is_key_player:
                    report.key_players_out.append({
                        'name': player.get('display_name', 'Unknown'),
                        'position': position,
                        'return_date': injury.get('expected_return_date'),
                        'injury_type': injury.get('injury', {}).get('name', 'Unknown')
                    })
            
            # Calculate impact rating (0-10)
            impact = 0
            if report.missing_goalkeeper:
                impact += 3
            impact += min(report.missing_key_defenders * 1.5, 4)
            impact += min(len([p for p in report.key_players_out if 'Forward' in p.get('position', '')]) * 2, 3)
            
            report.impact_rating = min(impact, 10)
            
            return report
            
        except Exception as e:
            logger.error(f"Error getting injury report: {str(e)}")
            return InjuryReport()
    
    def _get_team_motivation(self, team_id: int, league_id: int) -> TeamMotivation:
        """Analyze team motivation based on league standings"""
        try:
            # Get current season
            season_id = self.client.get_current_season_id(league_id)
            if not season_id:
                return TeamMotivation()
            
            # Get standings
            standings_data = self.client.get_standings_by_season(season_id, include=['participant'])
            
            if not standings_data or 'data' not in standings_data:
                return TeamMotivation()
            
            motivation = TeamMotivation()
            standings = standings_data['data']
            
            # Find team position
            team_standing = None
            total_teams = len(standings)
            
            for i, standing in enumerate(standings):
                if standing.get('participant_id') == team_id:
                    team_standing = standing
                    motivation.league_position = i + 1
                    break
            
            if not team_standing:
                return motivation
            
            # Calculate motivation factors
            motivation.points_from_top = standings[0]['points'] - team_standing['points'] if standings else 0
            motivation.points_from_relegation = team_standing['points'] - standings[-3]['points'] if len(standings) > 3 else 0
            
            # Determine race involvement
            if motivation.league_position <= 3 and motivation.points_from_top <= 10:
                motivation.title_race = True
                motivation.motivation_score = 9.0
            elif motivation.league_position <= 6:
                motivation.european_spots_race = True
                motivation.motivation_score = 7.5
            elif motivation.league_position >= total_teams - 3:
                motivation.relegation_battle = True
                motivation.motivation_score = 8.5
            else:
                motivation.motivation_score = 5.0  # Mid-table
            
            return motivation
            
        except Exception as e:
            logger.error(f"Error getting team motivation: {str(e)}")
            return TeamMotivation()
    
    def _get_sportmonks_prediction(self, fixture_id: int) -> Optional[Dict]:
        """Get base prediction from SportMonks"""
        try:
            result = self.client.get_fixture_with_predictions(fixture_id)
            if result and 'data' in result:
                return result['data'].get('predictions', {})
            return None
        except Exception as e:
            logger.error(f"Error getting SportMonks prediction: {str(e)}")
            return None
    
    def _calculate_prediction(self, **kwargs) -> AdvancedPrediction:
        """Calculate final prediction based on all factors"""
        fixture_data = kwargs['fixture_data']
        home_team = kwargs['home_team']
        away_team = kwargs['away_team']
        home_form = kwargs.get('home_form', TeamForm())
        away_form = kwargs.get('away_form', TeamForm())
        h2h_stats = kwargs.get('h2h_stats', HeadToHeadStats())
        home_injuries = kwargs.get('home_injuries', InjuryReport())
        away_injuries = kwargs.get('away_injuries', InjuryReport())
        home_motivation = kwargs.get('home_motivation', TeamMotivation())
        away_motivation = kwargs.get('away_motivation', TeamMotivation())
        base_prediction = kwargs.get('base_prediction', {})
        
        # Initialize factors
        factors = {
            'form': {'home': 0, 'away': 0, 'weight': self.WEIGHTS['recent_form']},
            'h2h': {'home': 0, 'away': 0, 'weight': self.WEIGHTS['head_to_head']},
            'injuries': {'home': 0, 'away': 0, 'weight': self.WEIGHTS['injuries']},
            'home_advantage': {'home': 0.6, 'away': 0.4, 'weight': self.WEIGHTS['home_advantage']},
            'motivation': {'home': 0, 'away': 0, 'weight': self.WEIGHTS['motivation']}
        }
        
        # 1. Form Analysis
        if home_form and away_form:
            factors['form']['home'] = home_form.form_rating / 10
            factors['form']['away'] = away_form.form_rating / 10
        
        # 2. Head-to-Head Analysis
        if h2h_stats and h2h_stats.total_matches > 0:
            total_h2h = h2h_stats.home_wins + h2h_stats.away_wins + h2h_stats.draws
            factors['h2h']['home'] = h2h_stats.home_wins / total_h2h
            factors['h2h']['away'] = h2h_stats.away_wins / total_h2h
        else:
            # No H2H data, use equal weights
            factors['h2h']['home'] = 0.5
            factors['h2h']['away'] = 0.5
        
        # 3. Injury Impact (inverse - more injuries = lower score)
        if home_injuries and away_injuries:
            home_injury_factor = 1 - (home_injuries.impact_rating / 10)
            away_injury_factor = 1 - (away_injuries.impact_rating / 10)
            factors['injuries']['home'] = home_injury_factor
            factors['injuries']['away'] = away_injury_factor
        
        # 4. Motivation
        if home_motivation and away_motivation:
            factors['motivation']['home'] = home_motivation.motivation_score / 10
            factors['motivation']['away'] = away_motivation.motivation_score / 10
        
        # Calculate weighted probabilities
        home_score = 0
        away_score = 0
        
        for factor, values in factors.items():
            home_score += values['home'] * values['weight']
            away_score += values['away'] * values['weight']
        
        # Normalize to probabilities
        total_score = home_score + away_score
        home_win_prob = (home_score / total_score) * 0.85  # 85% for win probabilities
        away_win_prob = (away_score / total_score) * 0.85
        draw_prob = 0.15  # Base draw probability
        
        # Adjust based on historical draw rate
        if h2h_stats and h2h_stats.total_matches > 0:
            historical_draw_rate = h2h_stats.draws / h2h_stats.total_matches
            draw_prob = 0.1 + (historical_draw_rate * 0.2)  # Weighted historical draw rate
        
        # Ensure probabilities sum to 100%
        total_prob = home_win_prob + away_win_prob + draw_prob
        home_win_prob = (home_win_prob / total_prob) * 100
        away_win_prob = (away_win_prob / total_prob) * 100
        draw_prob = (draw_prob / total_prob) * 100
        
        # Goal predictions
        home_goals = 1.3  # Base home goals
        away_goals = 1.1  # Base away goals
        
        if home_form and away_form:
            home_goals = (home_form.avg_goals_per_match * 0.7) + (away_form.goals_conceded / max(len(away_form.last_5_results), 1) * 0.3)
            away_goals = (away_form.avg_goals_per_match * 0.7) + (home_form.goals_conceded / max(len(home_form.last_5_results), 1) * 0.3)
        
        # Adjust for injuries
        home_goals *= (1 - home_injuries.impact_rating / 20)  # Max 50% reduction
        away_goals *= (1 - away_injuries.impact_rating / 20)
        
        # BTTS and Over/Under calculations
        btts_prob = 50  # Base
        if home_form and away_form:
            home_scoring_rate = min(len([g for g in home_form.last_5_goals_scored if g > 0]) / max(len(home_form.last_5_goals_scored), 1), 1)
            away_scoring_rate = min(len([g for g in away_form.last_5_goals_scored if g > 0]) / max(len(away_form.last_5_goals_scored), 1), 1)
            btts_prob = home_scoring_rate * away_scoring_rate * 100
        
        total_goals = home_goals + away_goals
        over_25_prob = self._calculate_poisson_probability(total_goals, 2.5, over=True)
        over_35_prob = self._calculate_poisson_probability(total_goals, 3.5, over=True)
        under_25_prob = 100 - over_25_prob
        
        # Calculate confidence score
        data_quality_scores = [
            1 if home_form and len(home_form.last_5_results) >= 3 else 0,
            1 if away_form and len(away_form.last_5_results) >= 3 else 0,
            1 if h2h_stats and h2h_stats.total_matches >= 3 else 0,
            1 if home_injuries is not None else 0,
            1 if away_injuries is not None else 0,
            1 if home_motivation is not None else 0,
            1 if away_motivation is not None else 0
        ]
        
        confidence = (sum(data_quality_scores) / len(data_quality_scores)) * 100
        
        # Generate prediction summary
        summary = self._generate_summary(
            home_team=home_team['name'],
            away_team=away_team['name'],
            home_win_prob=home_win_prob,
            away_win_prob=away_win_prob,
            draw_prob=draw_prob,
            home_form=home_form,
            away_form=away_form,
            h2h_stats=h2h_stats,
            home_injuries=home_injuries,
            away_injuries=away_injuries
        )
        
        # Identify value bets
        value_bets = self._identify_value_bets(
            home_win_prob=home_win_prob,
            away_win_prob=away_win_prob,
            draw_prob=draw_prob,
            btts_prob=btts_prob,
            over_25_prob=over_25_prob,
            over_35_prob=over_35_prob
        )
        
        return AdvancedPrediction(
            fixture_id=fixture_data['id'],
            home_team=home_team['name'],
            away_team=away_team['name'],
            date=fixture_data.get('starting_at', ''),
            win_probability_home=round(home_win_prob, 1),
            win_probability_away=round(away_win_prob, 1),
            draw_probability=round(draw_prob, 1),
            predicted_goals_home=round(home_goals, 1),
            predicted_goals_away=round(away_goals, 1),
            btts_probability=round(btts_prob, 1),
            over_25_probability=round(over_25_prob, 1),
            over_35_probability=round(over_35_prob, 1),
            under_25_probability=round(under_25_prob, 1),
            confidence_score=round(confidence, 1),
            prediction_summary=summary,
            value_bets=value_bets,
            data_sources={
                'form': {'home': home_form.__dict__ if home_form else {}, 'away': away_form.__dict__ if away_form else {}},
                'h2h': h2h_stats.__dict__ if h2h_stats else {},
                'injuries': {'home': home_injuries.__dict__ if home_injuries else {}, 'away': away_injuries.__dict__ if away_injuries else {}},
                'motivation': {'home': home_motivation.__dict__ if home_motivation else {}, 'away': away_motivation.__dict__ if away_motivation else {}},
                'base_prediction': base_prediction
            },
            factors_breakdown=factors
        )
    
    def _calculate_poisson_probability(self, expected_goals: float, threshold: float, over: bool = True) -> float:
        """Calculate probability of goals over/under threshold using Poisson distribution"""
        try:
            from scipy.stats import poisson
            
            if over:
                prob = 1 - poisson.cdf(int(threshold), expected_goals)
            else:
                prob = poisson.cdf(int(threshold), expected_goals)
            
            return prob * 100
        except ImportError:
            # Fallback to simple calculation if scipy not available
            if over:
                return 50 + (expected_goals - threshold) * 15
            else:
                return 50 - (expected_goals - threshold) * 15
    
    def _generate_summary(self, **kwargs) -> str:
        """Generate human-readable prediction summary"""
        home_team = kwargs['home_team']
        away_team = kwargs['away_team']
        home_win_prob = kwargs['home_win_prob']
        away_win_prob = kwargs['away_win_prob']
        draw_prob = kwargs['draw_prob']
        home_form = kwargs.get('home_form')
        away_form = kwargs.get('away_form')
        h2h_stats = kwargs.get('h2h_stats')
        home_injuries = kwargs.get('home_injuries')
        away_injuries = kwargs.get('away_injuries')
        
        # Determine likely outcome
        if home_win_prob > away_win_prob and home_win_prob > draw_prob:
            outcome = f"{home_team} are favorites to win"
            confidence = "high" if home_win_prob > 60 else "moderate"
        elif away_win_prob > home_win_prob and away_win_prob > draw_prob:
            outcome = f"{away_team} are favorites to win"
            confidence = "high" if away_win_prob > 60 else "moderate"
        else:
            outcome = "A draw is the most likely outcome"
            confidence = "moderate"
        
        summary_parts = [f"{outcome} with {confidence} confidence."]
        
        # Add form context
        if home_form and away_form:
            if home_form.form_rating > away_form.form_rating + 2:
                summary_parts.append(f"{home_team} are in significantly better form.")
            elif away_form.form_rating > home_form.form_rating + 2:
                summary_parts.append(f"{away_team} are in significantly better form.")
        
        # Add H2H context
        if h2h_stats and h2h_stats.total_matches >= 3:
            if h2h_stats.home_wins > h2h_stats.away_wins * 2:
                summary_parts.append(f"{home_team} have dominated recent meetings.")
            elif h2h_stats.away_wins > h2h_stats.home_wins * 2:
                summary_parts.append(f"{away_team} have dominated recent meetings.")
        
        # Add injury context
        if home_injuries and home_injuries.impact_rating > 5:
            summary_parts.append(f"{home_team} are hampered by key injuries.")
        if away_injuries and away_injuries.impact_rating > 5:
            summary_parts.append(f"{away_team} are hampered by key injuries.")
        
        return " ".join(summary_parts)
    
    def _identify_value_bets(self, **probs) -> List[Dict]:
        """Identify potential value betting opportunities"""
        value_bets = []
        
        # Match result value
        if probs['home_win_prob'] > 65:
            value_bets.append({
                'type': 'Match Result',
                'selection': 'Home Win',
                'probability': probs['home_win_prob'],
                'confidence': 'high'
            })
        elif probs['away_win_prob'] > 65:
            value_bets.append({
                'type': 'Match Result',
                'selection': 'Away Win',
                'probability': probs['away_win_prob'],
                'confidence': 'high'
            })
        
        # Goals markets
        if probs['over_25_prob'] > 70:
            value_bets.append({
                'type': 'Total Goals',
                'selection': 'Over 2.5',
                'probability': probs['over_25_prob'],
                'confidence': 'high'
            })
        elif probs['over_25_prob'] < 30:
            value_bets.append({
                'type': 'Total Goals',
                'selection': 'Under 2.5',
                'probability': 100 - probs['over_25_prob'],
                'confidence': 'high'
            })
        
        # BTTS
        if probs['btts_prob'] > 70:
            value_bets.append({
                'type': 'Both Teams to Score',
                'selection': 'Yes',
                'probability': probs['btts_prob'],
                'confidence': 'high'
            })
        elif probs['btts_prob'] < 30:
            value_bets.append({
                'type': 'Both Teams to Score',
                'selection': 'No',
                'probability': 100 - probs['btts_prob'],
                'confidence': 'high'
            })
        
        return value_bets