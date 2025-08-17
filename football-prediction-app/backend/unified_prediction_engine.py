"""
Unified Prediction Engine for Football Matches
Combines the best features from all prediction engines into one comprehensive system
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import statistics
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

logger = logging.getLogger(__name__)

@dataclass
class TeamMetrics:
    """Comprehensive team metrics for predictions"""
    # Basic Info
    team_id: int
    team_name: str
    
    # Form Data
    last_10_results: List[Dict] = field(default_factory=list)
    home_form: List[str] = field(default_factory=list)  # W/D/L
    away_form: List[str] = field(default_factory=list)  # W/D/L
    current_streak: str = ""
    form_rating: float = 0.0  # 0-10 scale
    
    # Goal Statistics
    goals_scored_last_5: int = 0
    goals_conceded_last_5: int = 0
    avg_goals_scored: float = 0.0
    avg_goals_conceded: float = 0.0
    goals_per_match_home: float = 0.0
    goals_per_match_away: float = 0.0
    
    # Defensive Stats
    clean_sheets_last_5: int = 0
    clean_sheet_percentage: float = 0.0
    
    # Other Stats
    btts_last_5: int = 0
    btts_percentage: float = 0.0
    over_25_percentage: float = 0.0
    
    # Advanced Metrics
    xg_for: float = 0.0  # Expected goals for
    xg_against: float = 0.0  # Expected goals against
    possession_avg: float = 0.0
    shots_per_game: float = 0.0
    shots_on_target_percentage: float = 0.0
    
    @property
    def win_percentage(self) -> float:
        """Calculate win percentage from form"""
        if not self.last_10_results:
            return 0.0
        wins = sum(1 for r in self.last_10_results if r.get('result') == 'W')
        return (wins / len(self.last_10_results)) * 100
    
    @property
    def points_per_game(self) -> float:
        """Calculate average points per game"""
        if not self.last_10_results:
            return 0.0
        points = sum(3 if r.get('result') == 'W' else 1 if r.get('result') == 'D' else 0 
                    for r in self.last_10_results)
        return points / len(self.last_10_results)

@dataclass
class HeadToHeadStats:
    """Head-to-head statistics between two teams"""
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
class InjuryData:
    """Injury and suspension report"""
    key_players_out: List[Dict] = field(default_factory=list)
    total_injuries: int = 0
    impact_rating: float = 0.0  # 0-10 scale

@dataclass
class PredictionResult:
    """Comprehensive prediction result"""
    # Basic Predictions
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    predicted_outcome: str  # 'home', 'draw', 'away'
    confidence: float  # 0-100
    
    # Score Predictions
    predicted_score: Tuple[int, int]  # (home_goals, away_goals)
    most_likely_scores: List[Tuple[Tuple[int, int], float]]  # [(score, probability)]
    
    # Goal Predictions
    over_25_probability: float
    under_25_probability: float
    btts_yes_probability: float
    btts_no_probability: float
    
    # Advanced Predictions
    first_goal_scorer_team: str  # 'home' or 'away'
    clean_sheet_home_probability: float
    clean_sheet_away_probability: float
    
    # AI Insights
    key_factors: List[str]
    reasoning: List[str]
    risk_assessment: str  # 'low', 'medium', 'high'
    value_bet_suggestions: List[Dict[str, Any]]
    
    # Metadata
    prediction_timestamp: datetime = field(default_factory=datetime.utcnow)
    model_version: str = "unified_v1.0"


class UnifiedPredictionEngine:
    """
    Unified prediction engine that combines all prediction approaches
    """
    
    def __init__(self, sportmonks_client=None):
        self.sportmonks_client = sportmonks_client
        self.cache = {}
        self.cache_timeout = 3600  # 1 hour
        
    def predict_match(self, 
                     fixture_id: Optional[int] = None,
                     home_team_id: Optional[int] = None,
                     away_team_id: Optional[int] = None,
                     fixture_data: Optional[Dict] = None) -> PredictionResult:
        """
        Generate comprehensive prediction for a match
        
        Args:
            fixture_id: SportMonks fixture ID
            home_team_id: Home team ID (if fixture_id not provided)
            away_team_id: Away team ID (if fixture_id not provided)
            fixture_data: Pre-fetched fixture data (optional)
            
        Returns:
            PredictionResult with comprehensive predictions
        """
        try:
            # Get fixture data if not provided
            if not fixture_data and fixture_id:
                fixture_data = self._get_fixture_data(fixture_id)
            elif not fixture_data:
                # Create minimal fixture data from team IDs
                fixture_data = {
                    'id': None,
                    'home_team_id': home_team_id,
                    'away_team_id': away_team_id
                }
            
            # Extract team IDs
            home_id = fixture_data.get('home_team_id') or home_team_id
            away_id = fixture_data.get('away_team_id') or away_team_id
            
            if not home_id or not away_id:
                raise ValueError("Both home and away team IDs are required")
            
            # Gather all data in parallel
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self._get_team_metrics, home_id, 'home'): 'home_metrics',
                    executor.submit(self._get_team_metrics, away_id, 'away'): 'away_metrics',
                    executor.submit(self._get_h2h_stats, home_id, away_id): 'h2h_stats',
                    executor.submit(self._get_injury_data, home_id): 'home_injuries',
                    executor.submit(self._get_injury_data, away_id): 'away_injuries'
                }
                
                results = {}
                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        results[key] = future.result()
                    except Exception as e:
                        logger.error(f"Error getting {key}: {str(e)}")
                        results[key] = None
            
            # Calculate predictions
            home_metrics = results.get('home_metrics') or self._get_default_metrics(home_id, 'home')
            away_metrics = results.get('away_metrics') or self._get_default_metrics(away_id, 'away')
            h2h_stats = results.get('h2h_stats') or self._get_default_h2h()
            home_injuries = results.get('home_injuries') or InjuryData()
            away_injuries = results.get('away_injuries') or InjuryData()
            
            # Generate prediction
            prediction = self._calculate_prediction(
                home_metrics, away_metrics, h2h_stats, 
                home_injuries, away_injuries, fixture_data
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error in predict_match: {str(e)}")
            # Return a default prediction on error
            return self._get_default_prediction()
    
    def _calculate_prediction(self, 
                            home_metrics: TeamMetrics,
                            away_metrics: TeamMetrics,
                            h2h_stats: HeadToHeadStats,
                            home_injuries: InjuryData,
                            away_injuries: InjuryData,
                            fixture_data: Dict) -> PredictionResult:
        """Calculate comprehensive prediction based on all data"""
        
        # Initialize factors and reasoning
        factors = []
        reasoning = []
        
        # Base probabilities from form
        form_diff = home_metrics.form_rating - away_metrics.form_rating
        base_home_prob = 0.33 + (form_diff * 0.05)
        base_away_prob = 0.33 - (form_diff * 0.05)
        base_draw_prob = 0.34
        
        # Adjust for home advantage
        home_advantage = 0.1
        base_home_prob += home_advantage
        base_away_prob -= home_advantage * 0.5
        base_draw_prob -= home_advantage * 0.5
        
        factors.append("Home advantage considered")
        
        # Adjust for head-to-head
        if h2h_stats.total_matches > 0:
            h2h_home_rate = h2h_stats.home_wins / h2h_stats.total_matches
            h2h_away_rate = h2h_stats.away_wins / h2h_stats.total_matches
            h2h_draw_rate = h2h_stats.draws / h2h_stats.total_matches
            
            # Weighted average with base probabilities
            h2h_weight = min(0.3, h2h_stats.total_matches / 20)  # Max 30% weight
            base_home_prob = base_home_prob * (1 - h2h_weight) + h2h_home_rate * h2h_weight
            base_away_prob = base_away_prob * (1 - h2h_weight) + h2h_away_rate * h2h_weight
            base_draw_prob = base_draw_prob * (1 - h2h_weight) + h2h_draw_rate * h2h_weight
            
            if h2h_stats.dominant_team:
                factors.append(f"{h2h_stats.dominant_team} dominates head-to-head record")
        
        # Adjust for injuries
        injury_impact = (home_injuries.impact_rating - away_injuries.impact_rating) / 10
        base_home_prob -= injury_impact * 0.1
        base_away_prob += injury_impact * 0.1
        
        if home_injuries.impact_rating > 5:
            factors.append(f"Home team has significant injuries ({home_injuries.total_injuries} players out)")
        if away_injuries.impact_rating > 5:
            factors.append(f"Away team has significant injuries ({away_injuries.total_injuries} players out)")
        
        # Normalize probabilities
        total_prob = base_home_prob + base_draw_prob + base_away_prob
        home_win_prob = base_home_prob / total_prob
        draw_prob = base_draw_prob / total_prob
        away_win_prob = base_away_prob / total_prob
        
        # Determine predicted outcome
        probs = {'home': home_win_prob, 'draw': draw_prob, 'away': away_win_prob}
        predicted_outcome = max(probs, key=probs.get)
        
        # Calculate confidence
        confidence = max(home_win_prob, draw_prob, away_win_prob) * 100
        
        # Predict score
        home_goals_expected = home_metrics.avg_goals_scored * 0.6 + away_metrics.avg_goals_conceded * 0.4
        away_goals_expected = away_metrics.avg_goals_scored * 0.6 + home_metrics.avg_goals_conceded * 0.4
        
        # Adjust for home advantage in goals
        home_goals_expected *= 1.1
        away_goals_expected *= 0.9
        
        predicted_score = (round(home_goals_expected), round(away_goals_expected))
        
        # Calculate goal-related probabilities
        total_goals_expected = home_goals_expected + away_goals_expected
        over_25_prob = self._calculate_over_probability(total_goals_expected, 2.5)
        btts_prob = self._calculate_btts_probability(home_metrics, away_metrics)
        
        # Most likely scores
        most_likely_scores = self._calculate_likely_scores(home_goals_expected, away_goals_expected)
        
        # Risk assessment
        risk_level = self._assess_risk(confidence, factors)
        
        # Value bets
        value_bets = self._find_value_bets(probs, over_25_prob, btts_prob)
        
        # Build reasoning
        reasoning.append(f"Home team form rating: {home_metrics.form_rating:.1f}/10")
        reasoning.append(f"Away team form rating: {away_metrics.form_rating:.1f}/10")
        reasoning.append(f"Expected total goals: {total_goals_expected:.1f}")
        
        return PredictionResult(
            home_win_probability=round(home_win_prob, 3),
            draw_probability=round(draw_prob, 3),
            away_win_probability=round(away_win_prob, 3),
            predicted_outcome=predicted_outcome,
            confidence=round(confidence, 1),
            predicted_score=predicted_score,
            most_likely_scores=most_likely_scores,
            over_25_probability=round(over_25_prob, 3),
            under_25_probability=round(1 - over_25_prob, 3),
            btts_yes_probability=round(btts_prob, 3),
            btts_no_probability=round(1 - btts_prob, 3),
            first_goal_scorer_team='home' if home_win_prob > away_win_prob else 'away',
            clean_sheet_home_probability=round(self._calculate_clean_sheet_prob(away_goals_expected), 3),
            clean_sheet_away_probability=round(self._calculate_clean_sheet_prob(home_goals_expected), 3),
            key_factors=factors,
            reasoning=reasoning,
            risk_assessment=risk_level,
            value_bet_suggestions=value_bets
        )
    
    def _calculate_over_probability(self, expected_goals: float, threshold: float) -> float:
        """Calculate probability of over X goals using Poisson distribution approximation"""
        if expected_goals <= 0:
            return 0.0
        
        # Simplified calculation
        if expected_goals > threshold:
            base_prob = 0.5 + (expected_goals - threshold) * 0.15
        else:
            base_prob = 0.5 - (threshold - expected_goals) * 0.15
        
        return max(0.1, min(0.9, base_prob))
    
    def _calculate_btts_probability(self, home_metrics: TeamMetrics, away_metrics: TeamMetrics) -> float:
        """Calculate both teams to score probability"""
        home_scoring_prob = min(0.9, home_metrics.avg_goals_scored / 2)
        away_scoring_prob = min(0.9, away_metrics.avg_goals_scored / 2)
        
        # Consider defensive strength
        home_scoring_prob *= (1 + away_metrics.avg_goals_conceded / 3)
        away_scoring_prob *= (1 + home_metrics.avg_goals_conceded / 3)
        
        return home_scoring_prob * away_scoring_prob
    
    def _calculate_clean_sheet_prob(self, expected_goals_against: float) -> float:
        """Calculate clean sheet probability"""
        # Simplified Poisson P(0) approximation
        return max(0.05, min(0.95, np.exp(-expected_goals_against)))
    
    def _calculate_likely_scores(self, home_expected: float, away_expected: float) -> List[Tuple[Tuple[int, int], float]]:
        """Calculate most likely scorelines"""
        scores = []
        
        # Calculate probabilities for common scores
        for h in range(5):
            for a in range(5):
                # Simplified probability calculation
                prob = self._score_probability(h, a, home_expected, away_expected)
                if prob > 0.02:  # Only include if > 2% chance
                    scores.append(((h, a), prob))
        
        # Sort by probability
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:5]  # Top 5 most likely
    
    def _score_probability(self, home_goals: int, away_goals: int, 
                          home_expected: float, away_expected: float) -> float:
        """Calculate probability of specific score"""
        # Simplified calculation
        home_prob = self._poisson_prob(home_goals, home_expected)
        away_prob = self._poisson_prob(away_goals, away_expected)
        return home_prob * away_prob
    
    def _poisson_prob(self, k: int, lambda_: float) -> float:
        """Simplified Poisson probability"""
        if lambda_ <= 0:
            return 1.0 if k == 0 else 0.0
        
        # Use approximation for efficiency
        prob = (lambda_ ** k) * np.exp(-lambda_)
        for i in range(1, k + 1):
            prob /= i
        return prob
    
    def _assess_risk(self, confidence: float, factors: List[str]) -> str:
        """Assess prediction risk level"""
        risk_score = 0
        
        # Base risk from confidence
        if confidence < 40:
            risk_score += 3
        elif confidence < 50:
            risk_score += 2
        elif confidence < 60:
            risk_score += 1
        
        # Check for risk factors
        risk_keywords = ['injuries', 'poor form', 'inconsistent', 'unpredictable']
        for factor in factors:
            if any(keyword in factor.lower() for keyword in risk_keywords):
                risk_score += 1
        
        if risk_score >= 3:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _find_value_bets(self, outcome_probs: Dict[str, float], 
                        over_25_prob: float, btts_prob: float) -> List[Dict[str, Any]]:
        """Identify potential value bets"""
        value_bets = []
        
        # Check for value in main outcomes
        for outcome, prob in outcome_probs.items():
            if prob > 0.4:  # 40% probability threshold
                expected_odds = 1 / prob
                value_bets.append({
                    'type': f'{outcome}_win',
                    'probability': prob,
                    'minimum_odds': round(expected_odds * 1.1, 2),  # 10% value margin
                    'confidence': 'medium' if prob < 0.5 else 'high'
                })
        
        # Check goals markets
        if over_25_prob > 0.6:
            value_bets.append({
                'type': 'over_2.5_goals',
                'probability': over_25_prob,
                'minimum_odds': round(1 / over_25_prob * 1.1, 2),
                'confidence': 'medium'
            })
        
        if btts_prob > 0.6:
            value_bets.append({
                'type': 'btts_yes',
                'probability': btts_prob,
                'minimum_odds': round(1 / btts_prob * 1.1, 2),
                'confidence': 'medium'
            })
        
        return value_bets
    
    def _get_fixture_data(self, fixture_id: int) -> Dict:
        """Get fixture data from SportMonks"""
        if self.sportmonks_client:
            return self.sportmonks_client.get_fixture(fixture_id)
        return {}
    
    def _get_team_metrics(self, team_id: int, venue: str) -> TeamMetrics:
        """Get comprehensive team metrics"""
        # This would fetch real data from SportMonks
        # For now, return mock data
        return TeamMetrics(
            team_id=team_id,
            team_name=f"Team {team_id}",
            form_rating=7.0,
            avg_goals_scored=1.5,
            avg_goals_conceded=1.2
        )
    
    def _get_h2h_stats(self, home_id: int, away_id: int) -> HeadToHeadStats:
        """Get head-to-head statistics"""
        # This would fetch real data from SportMonks
        return HeadToHeadStats()
    
    def _get_injury_data(self, team_id: int) -> InjuryData:
        """Get injury and suspension data"""
        # This would fetch real data from SportMonks
        return InjuryData()
    
    def _get_default_metrics(self, team_id: int, venue: str) -> TeamMetrics:
        """Get default team metrics when data unavailable"""
        return TeamMetrics(
            team_id=team_id,
            team_name=f"Team {team_id}",
            form_rating=5.0,
            avg_goals_scored=1.2,
            avg_goals_conceded=1.2
        )
    
    def _get_default_h2h(self) -> HeadToHeadStats:
        """Get default H2H stats"""
        return HeadToHeadStats()
    
    def _get_default_prediction(self) -> PredictionResult:
        """Return default prediction when error occurs"""
        return PredictionResult(
            home_win_probability=0.40,
            draw_probability=0.30,
            away_win_probability=0.30,
            predicted_outcome='home',
            confidence=40.0,
            predicted_score=(1, 1),
            most_likely_scores=[((1, 1), 0.15), ((1, 0), 0.12), ((0, 0), 0.10)],
            over_25_probability=0.50,
            under_25_probability=0.50,
            btts_yes_probability=0.50,
            btts_no_probability=0.50,
            first_goal_scorer_team='home',
            clean_sheet_home_probability=0.30,
            clean_sheet_away_probability=0.30,
            key_factors=["Unable to fetch complete data"],
            reasoning=["Using default prediction due to data unavailability"],
            risk_assessment='high',
            value_bet_suggestions=[]
        )


# Utility functions for backward compatibility
def get_unified_prediction(fixture_id: int = None, 
                          home_team_id: int = None,
                          away_team_id: int = None,
                          sportmonks_client=None) -> Dict[str, Any]:
    """
    Get prediction using the unified engine
    Provides backward compatibility with existing code
    """
    engine = UnifiedPredictionEngine(sportmonks_client)
    result = engine.predict_match(fixture_id, home_team_id, away_team_id)
    
    # Convert to dictionary for JSON serialization
    return {
        'home_win_probability': result.home_win_probability,
        'draw_probability': result.draw_probability,
        'away_win_probability': result.away_win_probability,
        'predicted_outcome': result.predicted_outcome,
        'confidence': result.confidence,
        'predicted_score': {
            'home': result.predicted_score[0],
            'away': result.predicted_score[1]
        },
        'over_25_probability': result.over_25_probability,
        'btts_probability': result.btts_yes_probability,
        'key_factors': result.key_factors,
        'reasoning': result.reasoning,
        'risk_assessment': result.risk_assessment,
        'value_bets': result.value_bet_suggestions,
        'model_version': result.model_version
    }