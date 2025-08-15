"""
Enhanced Prediction Engine for Football Matches
Combines multiple data sources to generate AI-powered predictions
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

logger = logging.getLogger(__name__)

@dataclass
class TeamForm:
    """Recent form data for a team"""
    last_5_results: List[str] = field(default_factory=list)  # W/D/L
    goals_scored: int = 0
    goals_conceded: int = 0
    clean_sheets: int = 0
    btts_count: int = 0
    avg_goals_per_match: float = 0.0
    form_rating: float = 0.0  # 0-10 scale

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

@dataclass
class InjuryReport:
    """Injury and suspension data for a team"""
    key_players_out: List[Dict] = field(default_factory=list)
    total_injuries: int = 0
    impact_rating: float = 0.0  # 0-10 scale (10 = severe impact)

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

@dataclass
class EnhancedPrediction:
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
    confidence_score: float
    prediction_summary: str
    data_sources: Dict = field(default_factory=dict)

class EnhancedPredictionEngine:
    """
    AI-powered prediction engine that combines multiple data sources
    """
    
    # Weights for different prediction factors (total = 100%)
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
    
    def generate_prediction(self, fixture_id: int) -> Optional[EnhancedPrediction]:
        """
        Generate enhanced prediction for a fixture by aggregating multiple data sources
        """
        try:
            # Get fixture details
            fixture_data = self._get_fixture_details(fixture_id)
            if not fixture_data:
                return None
            
            home_team_id = fixture_data['home_team_id']
            away_team_id = fixture_data['away_team_id']
            
            # Fetch all data sources in parallel
            futures = {
                self.executor.submit(self._get_team_form, home_team_id, 'home'): 'home_form',
                self.executor.submit(self._get_team_form, away_team_id, 'away'): 'away_form',
                self.executor.submit(self._get_head_to_head, home_team_id, away_team_id): 'h2h',
                self.executor.submit(self._get_injuries, home_team_id, 'home'): 'home_injuries',
                self.executor.submit(self._get_injuries, away_team_id, 'away'): 'away_injuries',
                self.executor.submit(self._get_team_motivation, home_team_id, fixture_data['league_id'], 'home'): 'home_motivation',
                self.executor.submit(self._get_team_motivation, away_team_id, fixture_data['league_id'], 'away'): 'away_motivation',
                self.executor.submit(self._get_sportmonks_prediction, fixture_id): 'sportmonks_pred'
            }
            
            # Collect results
            data_sources = {}
            for future in as_completed(futures):
                key = futures[future]
                try:
                    data_sources[key] = future.result()
                except Exception as e:
                    logger.error(f"Error fetching {key}: {str(e)}")
                    data_sources[key] = None
            
            # Calculate weighted prediction
            prediction = self._calculate_weighted_prediction(
                fixture_data,
                data_sources
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error generating prediction for fixture {fixture_id}: {str(e)}")
            return None
    
    def _get_fixture_details(self, fixture_id: int) -> Optional[Dict]:
        """Get basic fixture information"""
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
                'venue_id': fixture.get('venue_id')
            }
        except Exception as e:
            logger.error(f"Error fetching fixture details: {str(e)}")
            return None
    
    def _get_team_form(self, team_id: int, side: str) -> TeamForm:
        """Get recent form for a team"""
        try:
            # Get last 10 matches
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            
            response = self.client.get(
                f'fixtures/between/{start_date.strftime("%Y-%m-%d")}/{end_date.strftime("%Y-%m-%d")}/{team_id}',
                params={'include': 'participants;scores;state'}
            )
            
            if not response or 'data' not in response:
                return TeamForm()
            
            fixtures = sorted(response['data'], key=lambda x: x['starting_at'], reverse=True)[:10]
            
            form = TeamForm()
            for fixture in fixtures[:5]:  # Last 5 for form string
                if fixture.get('state_id') != 5:  # Only finished matches
                    continue
                
                participants = fixture.get('participants', [])
                team_participant = next((p for p in participants if p['id'] == team_id), None)
                if not team_participant:
                    continue
                
                is_home = team_participant.get('meta', {}).get('location') == 'home'
                scores = fixture.get('scores', [])
                
                if scores:
                    score = scores[0].get('score', {}).get('participant', {})
                    team_goals = score.get('home' if is_home else 'away', 0)
                    opponent_goals = score.get('away' if is_home else 'home', 0)
                    
                    form.goals_scored += team_goals
                    form.goals_conceded += opponent_goals
                    
                    if team_goals > opponent_goals:
                        form.last_5_results.append('W')
                    elif team_goals < opponent_goals:
                        form.last_5_results.append('L')
                    else:
                        form.last_5_results.append('D')
                    
                    if opponent_goals == 0:
                        form.clean_sheets += 1
                    if team_goals > 0 and opponent_goals > 0:
                        form.btts_count += 1
            
            # Calculate metrics
            matches_played = len(form.last_5_results)
            if matches_played > 0:
                form.avg_goals_per_match = form.goals_scored / matches_played
                wins = form.last_5_results.count('W')
                draws = form.last_5_results.count('D')
                form.form_rating = (wins * 3 + draws) / (matches_played * 3) * 10
            
            return form
            
        except Exception as e:
            logger.error(f"Error fetching team form: {str(e)}")
            return TeamForm()
    
    def _get_head_to_head(self, home_team_id: int, away_team_id: int) -> HeadToHeadStats:
        """Get head-to-head statistics"""
        try:
            response = self.client.get(
                f'fixtures/head-to-head/{home_team_id}/{away_team_id}',
                params={'include': 'participants;scores;state'}
            )
            
            if not response or 'data' not in response:
                return HeadToHeadStats()
            
            h2h = HeadToHeadStats()
            total_goals = 0
            
            for fixture in response['data'][:10]:  # Last 10 meetings
                if fixture.get('state_id') != 5:  # Only finished matches
                    continue
                
                h2h.total_matches += 1
                participants = fixture.get('participants', [])
                home_in_fixture = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
                
                scores = fixture.get('scores', [])
                if scores:
                    score = scores[0].get('score', {}).get('participant', {})
                    home_goals = score.get('home', 0)
                    away_goals = score.get('away', 0)
                    
                    total_goals += home_goals + away_goals
                    
                    if home_goals > 0 and away_goals > 0:
                        h2h.btts_percentage += 1
                    if home_goals + away_goals > 2.5:
                        h2h.over_25_percentage += 1
                    
                    # Determine winner relative to our home team
                    if home_in_fixture.get('id') == home_team_id:
                        if home_goals > away_goals:
                            h2h.home_wins += 1
                        elif away_goals > home_goals:
                            h2h.away_wins += 1
                        else:
                            h2h.draws += 1
                    else:
                        if away_goals > home_goals:
                            h2h.home_wins += 1
                        elif home_goals > away_goals:
                            h2h.away_wins += 1
                        else:
                            h2h.draws += 1
                    
                    h2h.recent_meetings.append({
                        'date': fixture.get('starting_at'),
                        'home_team': home_in_fixture.get('name'),
                        'score': f"{home_goals}-{away_goals}"
                    })
            
            if h2h.total_matches > 0:
                h2h.avg_goals_per_match = total_goals / h2h.total_matches
                h2h.btts_percentage = (h2h.btts_percentage / h2h.total_matches) * 100
                h2h.over_25_percentage = (h2h.over_25_percentage / h2h.total_matches) * 100
            
            return h2h
            
        except Exception as e:
            logger.error(f"Error fetching H2H data: {str(e)}")
            return HeadToHeadStats()
    
    def _get_injuries(self, team_id: int, side: str) -> InjuryReport:
        """Get injury and suspension data"""
        try:
            response = self.client.get(
                f'injuries/teams/{team_id}',
                params={'include': 'player'}
            )
            
            if not response or 'data' not in response:
                return InjuryReport()
            
            report = InjuryReport()
            
            for injury in response['data']:
                player = injury.get('player', {})
                if player.get('position', {}).get('name') in ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']:
                    report.key_players_out.append({
                        'name': player.get('display_name', 'Unknown'),
                        'position': player.get('position', {}).get('name'),
                        'reason': injury.get('reason', 'Unknown'),
                        'return_date': injury.get('return_date')
                    })
                    report.total_injuries += 1
            
            # Calculate impact rating based on number and importance of injuries
            if report.total_injuries == 0:
                report.impact_rating = 0.0
            elif report.total_injuries <= 2:
                report.impact_rating = 2.5
            elif report.total_injuries <= 4:
                report.impact_rating = 5.0
            else:
                report.impact_rating = min(7.5, 2.5 + report.total_injuries)
            
            return report
            
        except Exception as e:
            logger.error(f"Error fetching injuries: {str(e)}")
            return InjuryReport()
    
    def _get_team_motivation(self, team_id: int, league_id: int, side: str) -> TeamMotivation:
        """Get team motivation based on league position"""
        try:
            # Get current season
            season_id = self.client.get_current_season_id(league_id)
            if not season_id:
                return TeamMotivation()
            
            # Get standings
            response = self.client.get(
                f'standings/seasons/{season_id}',
                params={'include': 'participant'}
            )
            
            if not response or 'data' not in response:
                return TeamMotivation()
            
            standings = response['data']
            team_standing = next((s for s in standings if s.get('participant_id') == team_id), None)
            
            if not team_standing:
                return TeamMotivation()
            
            motivation = TeamMotivation()
            motivation.league_position = team_standing.get('position', 0)
            total_teams = len(standings)
            
            # Calculate points from top and relegation
            if motivation.league_position > 0:
                leader = standings[0]
                motivation.points_from_top = leader.get('points', 0) - team_standing.get('points', 0)
                
                if total_teams > 3:
                    relegation_position = total_teams - 2  # Usually 18th in 20-team league
                    if motivation.league_position < relegation_position:
                        relegation_team = standings[relegation_position - 1]
                        motivation.points_from_relegation = team_standing.get('points', 0) - relegation_team.get('points', 0)
            
            # Determine motivation factors
            if motivation.league_position <= 6 and motivation.points_from_top <= 10:
                motivation.title_race = True
                motivation.motivation_score = 9.0
            elif motivation.league_position <= 7:
                motivation.european_spots_race = True
                motivation.motivation_score = 7.5
            elif motivation.points_from_relegation <= 6:
                motivation.relegation_battle = True
                motivation.motivation_score = 8.5
            else:
                motivation.motivation_score = 5.0  # Mid-table
            
            return motivation
            
        except Exception as e:
            logger.error(f"Error fetching motivation data: {str(e)}")
            return TeamMotivation()
    
    def _get_sportmonks_prediction(self, fixture_id: int) -> Optional[Dict]:
        """Get SportMonks native prediction if available"""
        try:
            response = self.client.get_fixture_with_predictions(fixture_id)
            if not response or 'data' not in response:
                return None
            
            predictions = response['data'].get('predictions', [])
            parsed = {}
            
            for pred in predictions:
                pred_type = pred.get('type', {}).get('code', '')
                predictions_data = pred.get('predictions', {})
                
                if pred_type == 'fulltime-result-probability':
                    parsed['match_winner'] = {
                        'home': predictions_data.get('home', 0),
                        'draw': predictions_data.get('draw', 0),
                        'away': predictions_data.get('away', 0)
                    }
                elif pred_type == 'both-teams-to-score-probability':
                    parsed['btts'] = predictions_data.get('yes', 0)
                elif pred_type == 'over-under-2_5-probability':
                    parsed['over_25'] = predictions_data.get('yes', 0)
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error fetching SportMonks prediction: {str(e)}")
            return None
    
    def _calculate_weighted_prediction(self, fixture_data: Dict, data_sources: Dict) -> EnhancedPrediction:
        """Calculate final prediction using weighted factors"""
        
        # Initialize base probabilities
        home_win_prob = 33.33
        draw_prob = 33.33
        away_win_prob = 33.34
        
        # 1. Recent Form Analysis (40%)
        home_form = data_sources.get('home_form', TeamForm())
        away_form = data_sources.get('away_form', TeamForm())
        
        form_diff = home_form.form_rating - away_form.form_rating
        form_home_advantage = self._normalize_to_probability(form_diff, -5, 5)
        
        home_win_prob += form_home_advantage * self.WEIGHTS['recent_form'] * 100
        away_win_prob -= form_home_advantage * self.WEIGHTS['recent_form'] * 100
        
        # 2. Head-to-Head Analysis (20%)
        h2h = data_sources.get('h2h', HeadToHeadStats())
        if h2h.total_matches > 0:
            h2h_home_rate = h2h.home_wins / h2h.total_matches
            h2h_away_rate = h2h.away_wins / h2h.total_matches
            h2h_draw_rate = h2h.draws / h2h.total_matches
            
            home_win_prob += (h2h_home_rate - 0.33) * self.WEIGHTS['head_to_head'] * 100
            away_win_prob += (h2h_away_rate - 0.33) * self.WEIGHTS['head_to_head'] * 100
            draw_prob += (h2h_draw_rate - 0.33) * self.WEIGHTS['head_to_head'] * 100
        
        # 3. Injuries Impact (15%)
        home_injuries = data_sources.get('home_injuries', InjuryReport())
        away_injuries = data_sources.get('away_injuries', InjuryReport())
        
        injury_impact = (away_injuries.impact_rating - home_injuries.impact_rating) / 10
        home_win_prob += injury_impact * self.WEIGHTS['injuries'] * 100
        away_win_prob -= injury_impact * self.WEIGHTS['injuries'] * 100
        
        # 4. Home Advantage (10%)
        home_win_prob += self.WEIGHTS['home_advantage'] * 100 * 0.6  # 60% of weight to home
        draw_prob += self.WEIGHTS['home_advantage'] * 100 * 0.2      # 20% to draw
        away_win_prob += self.WEIGHTS['home_advantage'] * 100 * 0.2  # 20% to away
        
        # 5. Motivation (10%)
        home_motivation = data_sources.get('home_motivation', TeamMotivation())
        away_motivation = data_sources.get('away_motivation', TeamMotivation())
        
        motivation_diff = (home_motivation.motivation_score - away_motivation.motivation_score) / 10
        home_win_prob += motivation_diff * self.WEIGHTS['motivation'] * 100
        away_win_prob -= motivation_diff * self.WEIGHTS['motivation'] * 100
        
        # 6. Blend with SportMonks prediction if available (5%)
        sportmonks = data_sources.get('sportmonks_pred', {})
        if sportmonks and 'match_winner' in sportmonks:
            sm_weight = self.WEIGHTS['other_factors']
            home_win_prob = home_win_prob * (1 - sm_weight) + sportmonks['match_winner']['home'] * sm_weight
            draw_prob = draw_prob * (1 - sm_weight) + sportmonks['match_winner']['draw'] * sm_weight
            away_win_prob = away_win_prob * (1 - sm_weight) + sportmonks['match_winner']['away'] * sm_weight
        
        # Normalize probabilities
        total_prob = home_win_prob + draw_prob + away_win_prob
        home_win_prob = (home_win_prob / total_prob) * 100
        draw_prob = (draw_prob / total_prob) * 100
        away_win_prob = (away_win_prob / total_prob) * 100
        
        # Calculate expected goals
        home_expected_goals = home_form.avg_goals_per_match * 0.6 + (h2h.avg_goals_per_match / 2) * 0.4
        away_expected_goals = away_form.avg_goals_per_match * 0.6 + (h2h.avg_goals_per_match / 2) * 0.4
        
        # BTTS and Over 2.5 probabilities
        btts_prob = min(90, (home_form.btts_count / max(1, len(home_form.last_5_results)) * 50 +
                            away_form.btts_count / max(1, len(away_form.last_5_results)) * 50))
        
        if sportmonks and 'btts' in sportmonks:
            btts_prob = btts_prob * 0.7 + sportmonks['btts'] * 0.3
        
        over_25_prob = self._calculate_over_25_probability(home_expected_goals, away_expected_goals)
        if sportmonks and 'over_25' in sportmonks:
            over_25_prob = over_25_prob * 0.7 + sportmonks['over_25'] * 0.3
        
        # Calculate confidence score
        confidence = self._calculate_confidence_score(
            max(home_win_prob, draw_prob, away_win_prob),
            h2h.total_matches,
            len(home_form.last_5_results) + len(away_form.last_5_results)
        )
        
        # Generate summary
        summary = self._generate_prediction_summary(
            fixture_data,
            home_win_prob,
            draw_prob,
            away_win_prob,
            data_sources
        )
        
        return EnhancedPrediction(
            fixture_id=fixture_data['fixture_id'],
            home_team=fixture_data['home_team_name'],
            away_team=fixture_data['away_team_name'],
            date=fixture_data['date'],
            win_probability_home=round(home_win_prob, 2),
            win_probability_away=round(away_win_prob, 2),
            draw_probability=round(draw_prob, 2),
            predicted_goals_home=round(home_expected_goals, 1),
            predicted_goals_away=round(away_expected_goals, 1),
            btts_probability=round(btts_prob, 2),
            over_25_probability=round(over_25_prob, 2),
            confidence_score=round(confidence, 2),
            prediction_summary=summary,
            data_sources={
                'form': {'home': home_form.__dict__, 'away': away_form.__dict__},
                'h2h': h2h.__dict__,
                'injuries': {'home': home_injuries.__dict__, 'away': away_injuries.__dict__},
                'motivation': {'home': home_motivation.__dict__, 'away': away_motivation.__dict__}
            }
        )
    
    def _normalize_to_probability(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize a value to 0-1 probability range"""
        return max(0, min(1, (value - min_val) / (max_val - min_val)))
    
    def _calculate_over_25_probability(self, home_goals: float, away_goals: float) -> float:
        """Calculate probability of over 2.5 goals using Poisson distribution approximation"""
        total_expected = home_goals + away_goals
        if total_expected <= 1.5:
            return 20.0
        elif total_expected <= 2.0:
            return 35.0
        elif total_expected <= 2.5:
            return 50.0
        elif total_expected <= 3.0:
            return 65.0
        else:
            return min(85.0, 65.0 + (total_expected - 3.0) * 10)
    
    def _calculate_confidence_score(self, max_prob: float, h2h_matches: int, form_matches: int) -> float:
        """Calculate confidence in the prediction"""
        # Base confidence on probability strength
        prob_confidence = max_prob / 100 * 50  # 0-50 points
        
        # Data quality confidence
        data_confidence = 0
        if h2h_matches >= 5:
            data_confidence += 25
        elif h2h_matches >= 3:
            data_confidence += 15
        elif h2h_matches >= 1:
            data_confidence += 10
        
        if form_matches >= 8:
            data_confidence += 25
        elif form_matches >= 6:
            data_confidence += 15
        elif form_matches >= 4:
            data_confidence += 10
        
        return prob_confidence + data_confidence
    
    def _generate_prediction_summary(self, fixture_data: Dict, home_prob: float, 
                                   draw_prob: float, away_prob: float, 
                                   data_sources: Dict) -> str:
        """Generate human-readable prediction summary"""
        # Determine predicted outcome
        if home_prob > away_prob and home_prob > draw_prob:
            outcome = f"{fixture_data['home_team_name']} to win"
            prob = home_prob
        elif away_prob > home_prob and away_prob > draw_prob:
            outcome = f"{fixture_data['away_team_name']} to win"
            prob = away_prob
        else:
            outcome = "Draw"
            prob = draw_prob
        
        # Build summary
        summary_parts = [f"Predicted outcome: {outcome} ({prob:.1f}% probability)."]
        
        # Add key factors
        home_form = data_sources.get('home_form', TeamForm())
        away_form = data_sources.get('away_form', TeamForm())
        
        if home_form.form_rating > away_form.form_rating + 2:
            summary_parts.append(f"{fixture_data['home_team_name']} in excellent form.")
        elif away_form.form_rating > home_form.form_rating + 2:
            summary_parts.append(f"{fixture_data['away_team_name']} in excellent form.")
        
        h2h = data_sources.get('h2h', HeadToHeadStats())
        if h2h.total_matches > 0:
            if h2h.home_wins > h2h.away_wins * 1.5:
                summary_parts.append(f"H2H favors {fixture_data['home_team_name']}.")
            elif h2h.away_wins > h2h.home_wins * 1.5:
                summary_parts.append(f"H2H favors {fixture_data['away_team_name']}.")
        
        home_injuries = data_sources.get('home_injuries', InjuryReport())
        away_injuries = data_sources.get('away_injuries', InjuryReport())
        
        if home_injuries.impact_rating > 5:
            summary_parts.append(f"{fixture_data['home_team_name']} affected by injuries.")
        if away_injuries.impact_rating > 5:
            summary_parts.append(f"{fixture_data['away_team_name']} affected by injuries.")
        
        return " ".join(summary_parts)