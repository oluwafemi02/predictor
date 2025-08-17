import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sportmonks_api_v3 import SportMonksV3Client
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)

@dataclass
class TeamForm:
    """Team form data for predictions"""
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0
    matches_played: int = 0
    
    @property
    def win_percentage(self) -> float:
        return (self.wins / self.matches_played * 100) if self.matches_played > 0 else 0
    
    @property
    def goals_per_match(self) -> float:
        return self.goals_for / self.matches_played if self.matches_played > 0 else 0
    
    @property
    def goals_conceded_per_match(self) -> float:
        return self.goals_against / self.matches_played if self.matches_played > 0 else 0
    
    @property
    def points_per_match(self) -> float:
        return self.points / self.matches_played if self.matches_played > 0 else 0

@dataclass
class PredictionResult:
    """Prediction result with probabilities and reasoning"""
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    predicted_outcome: str  # 'home', 'draw', 'away'
    confidence: float
    reasoning: List[str]
    predicted_score: Tuple[int, int]  # (home_goals, away_goals)

class SimplePredictionEngine:
    """Simple but effective prediction engine for football matches"""
    
    def __init__(self):
        self.client = SportMonksV3Client()
        self.form_matches = 10  # Last N matches to consider for form
        
    def analyze_fixture(self, fixture_id: int) -> Optional[PredictionResult]:
        """Analyze a single fixture and return prediction"""
        try:
            # Get fixture details with all necessary data
            fixture_data = self.client.get_fixture_by_id(
                fixture_id,
                include='participants;league;venue;scores;lineups;events;statistics'
            )
            
            if not fixture_data or 'data' not in fixture_data:
                logger.error(f"No fixture data found for ID {fixture_id}")
                return None
            
            fixture = fixture_data['data']
            
            # Extract team IDs
            home_team_id = None
            away_team_id = None
            
            if 'participants' in fixture:
                for participant in fixture['participants']:
                    if participant.get('meta', {}).get('location') == 'home':
                        home_team_id = participant['id']
                    elif participant.get('meta', {}).get('location') == 'away':
                        away_team_id = participant['id']
            
            if not home_team_id or not away_team_id:
                logger.error("Could not extract team IDs from fixture")
                return None
            
            # Get team forms
            home_form = self._get_team_form(home_team_id)
            away_form = self._get_team_form(away_team_id)
            
            # Get head-to-head record
            h2h_stats = self._get_head_to_head_stats(home_team_id, away_team_id)
            
            # Calculate prediction
            prediction = self._calculate_prediction(home_form, away_form, h2h_stats)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error analyzing fixture {fixture_id}: {str(e)}")
            return None
    
    def _get_team_form(self, team_id: int) -> TeamForm:
        """Get team's recent form"""
        form = TeamForm()
        
        try:
            # Get team's recent fixtures
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
            
            fixtures_data = self.client.get_fixtures_by_date_range_for_team(
                start_date, end_date, team_id,
                include='scores;participants'
            )
            
            if not fixtures_data or 'data' not in fixtures_data:
                return form
            
            # Analyze last N matches
            fixtures = sorted(
                fixtures_data['data'],
                key=lambda x: x.get('starting_at', ''),
                reverse=True
            )[:self.form_matches]
            
            for fixture in fixtures:
                if fixture.get('state_id') != 5:  # Not finished
                    continue
                
                # Find team's role (home/away) and scores
                is_home = False
                team_score = 0
                opponent_score = 0
                
                scores = fixture.get('scores', [])
                participants = fixture.get('participants', [])
                
                for participant in participants:
                    if participant['id'] == team_id:
                        is_home = participant.get('meta', {}).get('location') == 'home'
                        break
                
                # Get full-time scores
                for score in scores:
                    if score.get('description') == 'FULLTIME':
                        if is_home:
                            team_score = score.get('score', {}).get('home', 0)
                            opponent_score = score.get('score', {}).get('away', 0)
                        else:
                            team_score = score.get('score', {}).get('away', 0)
                            opponent_score = score.get('score', {}).get('home', 0)
                        break
                
                # Update form stats
                form.goals_for += team_score
                form.goals_against += opponent_score
                form.matches_played += 1
                
                if team_score > opponent_score:
                    form.wins += 1
                    form.points += 3
                elif team_score == opponent_score:
                    form.draws += 1
                    form.points += 1
                else:
                    form.losses += 1
            
            return form
            
        except Exception as e:
            logger.error(f"Error getting team form for {team_id}: {str(e)}")
            return form
    
    def _get_head_to_head_stats(self, home_team_id: int, away_team_id: int) -> Dict:
        """Get head-to-head statistics between two teams"""
        stats = {
            'home_wins': 0,
            'draws': 0,
            'away_wins': 0,
            'total_matches': 0,
            'avg_goals': 0
        }
        
        try:
            h2h_data = self.client.get_fixtures_by_head_to_head(
                home_team_id, away_team_id,
                include='scores;participants'
            )
            
            if not h2h_data or 'data' not in h2h_data:
                return stats
            
            total_goals = 0
            
            for fixture in h2h_data['data'][:10]:  # Last 10 H2H matches
                if fixture.get('state_id') != 5:  # Not finished
                    continue
                
                # Get scores
                home_score = 0
                away_score = 0
                
                scores = fixture.get('scores', [])
                for score in scores:
                    if score.get('description') == 'FULLTIME':
                        home_score = score.get('score', {}).get('home', 0)
                        away_score = score.get('score', {}).get('away', 0)
                        break
                
                # Check which team was home in this fixture
                fixture_home_id = None
                for participant in fixture.get('participants', []):
                    if participant.get('meta', {}).get('location') == 'home':
                        fixture_home_id = participant['id']
                        break
                
                stats['total_matches'] += 1
                total_goals += home_score + away_score
                
                if home_score > away_score:
                    if fixture_home_id == home_team_id:
                        stats['home_wins'] += 1
                    else:
                        stats['away_wins'] += 1
                elif home_score < away_score:
                    if fixture_home_id == home_team_id:
                        stats['away_wins'] += 1
                    else:
                        stats['home_wins'] += 1
                else:
                    stats['draws'] += 1
            
            if stats['total_matches'] > 0:
                stats['avg_goals'] = total_goals / stats['total_matches']
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting H2H stats: {str(e)}")
            return stats
    
    def _calculate_prediction(self, home_form: TeamForm, away_form: TeamForm, h2h_stats: Dict) -> PredictionResult:
        """Calculate match prediction based on form and H2H"""
        reasoning = []
        
        # Base probabilities
        home_prob = 33.3
        draw_prob = 33.3
        away_prob = 33.3
        
        # Adjust based on form (40% weight)
        if home_form.matches_played > 0 and away_form.matches_played > 0:
            form_diff = home_form.points_per_match - away_form.points_per_match
            
            if form_diff > 0.5:
                home_prob += 15
                draw_prob -= 5
                away_prob -= 10
                reasoning.append(f"Home team in better form ({home_form.points_per_match:.2f} vs {away_form.points_per_match:.2f} points per match)")
            elif form_diff < -0.5:
                home_prob -= 10
                draw_prob -= 5
                away_prob += 15
                reasoning.append(f"Away team in better form ({away_form.points_per_match:.2f} vs {home_form.points_per_match:.2f} points per match)")
            else:
                reasoning.append("Both teams in similar form")
        
        # Adjust based on goals (20% weight)
        if home_form.matches_played > 0 and away_form.matches_played > 0:
            home_attack = home_form.goals_per_match
            away_attack = away_form.goals_per_match
            home_defense = home_form.goals_conceded_per_match
            away_defense = away_form.goals_conceded_per_match
            
            if home_attack > away_attack * 1.3:
                home_prob += 5
                away_prob -= 5
                reasoning.append(f"Home team more attacking ({home_attack:.2f} goals per match)")
            
            if home_defense < away_defense * 0.7:
                home_prob += 5
                away_prob -= 5
                reasoning.append(f"Home team better defensively ({home_defense:.2f} goals conceded per match)")
        
        # Adjust based on H2H (20% weight)
        if h2h_stats['total_matches'] >= 3:
            h2h_home_win_rate = h2h_stats['home_wins'] / h2h_stats['total_matches']
            h2h_away_win_rate = h2h_stats['away_wins'] / h2h_stats['total_matches']
            
            if h2h_home_win_rate > 0.5:
                home_prob += 10
                away_prob -= 10
                reasoning.append(f"Home team dominates H2H ({h2h_stats['home_wins']} wins in {h2h_stats['total_matches']} matches)")
            elif h2h_away_win_rate > 0.5:
                home_prob -= 10
                away_prob += 10
                reasoning.append(f"Away team dominates H2H ({h2h_stats['away_wins']} wins in {h2h_stats['total_matches']} matches)")
        
        # Home advantage (20% weight)
        home_prob += 10
        away_prob -= 5
        draw_prob -= 5
        reasoning.append("Home advantage considered")
        
        # Normalize probabilities
        total = home_prob + draw_prob + away_prob
        home_prob = (home_prob / total) * 100
        draw_prob = (draw_prob / total) * 100
        away_prob = (away_prob / total) * 100
        
        # Determine predicted outcome
        if home_prob > draw_prob and home_prob > away_prob:
            predicted_outcome = 'home'
        elif away_prob > draw_prob and away_prob > home_prob:
            predicted_outcome = 'away'
        else:
            predicted_outcome = 'draw'
        
        # Calculate confidence
        confidence = max(home_prob, draw_prob, away_prob) / 100
        
        # Predict score based on average goals
        home_goals = round(home_form.goals_per_match * 0.7 + away_form.goals_conceded_per_match * 0.3) if home_form.matches_played > 0 else 1
        away_goals = round(away_form.goals_per_match * 0.7 + home_form.goals_conceded_per_match * 0.3) if away_form.matches_played > 0 else 1
        
        # Adjust score based on prediction
        if predicted_outcome == 'home' and home_goals <= away_goals:
            home_goals = away_goals + 1
        elif predicted_outcome == 'away' and away_goals <= home_goals:
            away_goals = home_goals + 1
        elif predicted_outcome == 'draw' and home_goals != away_goals:
            home_goals = away_goals = min(home_goals, away_goals)
        
        return PredictionResult(
            home_win_probability=round(home_prob, 1),
            draw_probability=round(draw_prob, 1),
            away_win_probability=round(away_prob, 1),
            predicted_outcome=predicted_outcome,
            confidence=round(confidence, 2),
            reasoning=reasoning,
            predicted_score=(home_goals, away_goals)
        )
    
    def get_fixture_predictions(self, fixture_ids: List[int]) -> Dict[int, PredictionResult]:
        """Get predictions for multiple fixtures"""
        predictions = {}
        
        for fixture_id in fixture_ids:
            prediction = self.analyze_fixture(fixture_id)
            if prediction:
                predictions[fixture_id] = prediction
        
        return predictions