"""
Tests for Unified Prediction Engine
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from unified_prediction_engine import (
    UnifiedPredictionEngine, TeamMetrics, HeadToHeadStats,
    InjuryData, PredictionResult, get_unified_prediction
)


class TestTeamMetrics:
    """Test TeamMetrics dataclass"""
    
    def test_win_percentage_calculation(self):
        """Test win percentage calculation"""
        metrics = TeamMetrics(
            team_id=1,
            team_name="Test Team",
            last_10_results=[
                {'result': 'W'}, {'result': 'W'}, {'result': 'D'},
                {'result': 'L'}, {'result': 'W'}, {'result': 'W'},
                {'result': 'D'}, {'result': 'W'}, {'result': 'L'},
                {'result': 'W'}
            ]
        )
        assert metrics.win_percentage == 60.0  # 6 wins out of 10
    
    def test_win_percentage_no_results(self):
        """Test win percentage with no results"""
        metrics = TeamMetrics(team_id=1, team_name="Test Team")
        assert metrics.win_percentage == 0.0
    
    def test_points_per_game(self):
        """Test points per game calculation"""
        metrics = TeamMetrics(
            team_id=1,
            team_name="Test Team",
            last_10_results=[
                {'result': 'W'}, {'result': 'W'}, {'result': 'D'},
                {'result': 'L'}, {'result': 'D'}
            ]
        )
        # 2 wins (6 points) + 2 draws (2 points) = 8 points / 5 games = 1.6
        assert metrics.points_per_game == 1.6


class TestUnifiedPredictionEngine:
    """Test UnifiedPredictionEngine class"""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance"""
        return UnifiedPredictionEngine()
    
    @pytest.fixture
    def mock_sportmonks_client(self):
        """Create mock SportMonks client"""
        client = Mock()
        client.get_fixture.return_value = {
            'id': 123,
            'home_team_id': 1,
            'away_team_id': 2,
            'starting_at': '2024-08-17 15:00:00'
        }
        return client
    
    def test_predict_match_with_fixture_id(self, engine, mock_sportmonks_client):
        """Test predict_match with fixture ID"""
        engine.sportmonks_client = mock_sportmonks_client
        
        with patch.object(engine, '_get_team_metrics') as mock_metrics:
            mock_metrics.return_value = TeamMetrics(
                team_id=1,
                team_name="Home Team",
                form_rating=7.5,
                avg_goals_scored=1.8,
                avg_goals_conceded=0.9
            )
            
            result = engine.predict_match(fixture_id=123)
            
            assert isinstance(result, PredictionResult)
            assert result.home_win_probability + result.draw_probability + result.away_win_probability == pytest.approx(1.0)
            assert result.predicted_outcome in ['home', 'draw', 'away']
            assert 0 <= result.confidence <= 100
    
    def test_predict_match_with_team_ids(self, engine):
        """Test predict_match with team IDs"""
        result = engine.predict_match(home_team_id=1, away_team_id=2)
        
        assert isinstance(result, PredictionResult)
        assert result.predicted_score[0] >= 0
        assert result.predicted_score[1] >= 0
    
    def test_predict_match_missing_teams(self, engine):
        """Test predict_match with missing team IDs"""
        result = engine.predict_match()
        
        # Should return default prediction
        assert result.risk_assessment == 'high'
        assert 'Unable to fetch complete data' in result.key_factors
    
    def test_calculate_over_probability(self, engine):
        """Test over/under probability calculation"""
        # Test various scenarios
        assert engine._calculate_over_probability(3.0, 2.5) > 0.5
        assert engine._calculate_over_probability(2.0, 2.5) < 0.5
        assert engine._calculate_over_probability(0, 2.5) == 0.1  # Minimum
        assert engine._calculate_over_probability(6.0, 2.5) <= 0.9  # Maximum
    
    def test_calculate_btts_probability(self, engine):
        """Test both teams to score probability"""
        home_metrics = TeamMetrics(
            team_id=1,
            team_name="Home",
            avg_goals_scored=2.0,
            avg_goals_conceded=1.0
        )
        away_metrics = TeamMetrics(
            team_id=2,
            team_name="Away",
            avg_goals_scored=1.5,
            avg_goals_conceded=1.5
        )
        
        btts_prob = engine._calculate_btts_probability(home_metrics, away_metrics)
        assert 0 <= btts_prob <= 1
    
    def test_calculate_clean_sheet_probability(self, engine):
        """Test clean sheet probability calculation"""
        # Low goals against = high clean sheet probability
        assert engine._calculate_clean_sheet_prob(0.5) > 0.5
        # High goals against = low clean sheet probability
        assert engine._calculate_clean_sheet_prob(2.5) < 0.3
    
    def test_assess_risk(self, engine):
        """Test risk assessment"""
        # High confidence, no risk factors
        assert engine._assess_risk(70, ['Good form', 'Strong team']) == 'low'
        
        # Low confidence
        assert engine._assess_risk(35, []) == 'high'
        
        # Risk factors present
        factors = ['Significant injuries', 'Poor form recently']
        assert engine._assess_risk(55, factors) in ['medium', 'high']
    
    def test_find_value_bets(self, engine):
        """Test value bet identification"""
        outcome_probs = {'home': 0.65, 'draw': 0.20, 'away': 0.15}
        value_bets = engine._find_value_bets(outcome_probs, 0.75, 0.65)
        
        # Should find value in high probability outcomes
        assert len(value_bets) > 0
        home_bet = next((b for b in value_bets if b['type'] == 'home_win'), None)
        assert home_bet is not None
        assert home_bet['probability'] == 0.65
    
    def test_poisson_probability(self, engine):
        """Test Poisson probability calculation"""
        # P(X=0) when lambda=1 should be approximately e^-1
        prob = engine._poisson_prob(0, 1.0)
        assert prob == pytest.approx(0.368, rel=0.01)
        
        # Edge cases
        assert engine._poisson_prob(0, 0) == 1.0
        assert engine._poisson_prob(1, 0) == 0.0
    
    def test_score_probability(self, engine):
        """Test specific score probability"""
        prob = engine._score_probability(1, 1, 1.5, 1.2)
        assert 0 <= prob <= 1
    
    def test_calculate_likely_scores(self, engine):
        """Test most likely scores calculation"""
        scores = engine._calculate_likely_scores(1.5, 1.0)
        
        assert len(scores) <= 5
        assert all(isinstance(s[0], tuple) for s in scores)
        assert all(0 <= s[1] <= 1 for s in scores)
        # Should be sorted by probability
        if len(scores) > 1:
            assert scores[0][1] >= scores[1][1]
    
    @patch('unified_prediction_engine.ThreadPoolExecutor')
    def test_parallel_data_fetching(self, mock_executor, engine):
        """Test parallel data fetching"""
        # Mock the executor to return immediately
        mock_executor.return_value.__enter__.return_value.submit.return_value.result.return_value = TeamMetrics(
            team_id=1,
            team_name="Test",
            form_rating=5.0
        )
        
        result = engine.predict_match(home_team_id=1, away_team_id=2)
        assert isinstance(result, PredictionResult)
    
    def test_error_handling(self, engine):
        """Test error handling in prediction"""
        # Mock a method to raise an exception
        with patch.object(engine, '_calculate_prediction', side_effect=Exception("Test error")):
            result = engine.predict_match(home_team_id=1, away_team_id=2)
            
            # Should return default prediction
            assert result.risk_assessment == 'high'
            assert 'Using default prediction' in result.reasoning[0]


class TestBackwardCompatibility:
    """Test backward compatibility functions"""
    
    def test_get_unified_prediction(self):
        """Test get_unified_prediction utility function"""
        result = get_unified_prediction(home_team_id=1, away_team_id=2)
        
        assert isinstance(result, dict)
        assert 'home_win_probability' in result
        assert 'predicted_score' in result
        assert isinstance(result['predicted_score'], dict)
        assert 'home' in result['predicted_score']
        assert 'away' in result['predicted_score']
        assert result['model_version'] == 'unified_v1.0'
    
    def test_get_unified_prediction_with_client(self):
        """Test get_unified_prediction with SportMonks client"""
        mock_client = Mock()
        result = get_unified_prediction(
            fixture_id=123,
            sportmonks_client=mock_client
        )
        
        assert isinstance(result, dict)
        assert 'confidence' in result
        assert 'risk_assessment' in result


class TestIntegration:
    """Integration tests"""
    
    def test_full_prediction_flow(self):
        """Test complete prediction flow"""
        engine = UnifiedPredictionEngine()
        
        # Create mock data
        home_metrics = TeamMetrics(
            team_id=1,
            team_name="Manchester United",
            form_rating=8.0,
            avg_goals_scored=2.1,
            avg_goals_conceded=0.8,
            last_10_results=[{'result': 'W'} for _ in range(7)] + [{'result': 'D'} for _ in range(3)]
        )
        
        away_metrics = TeamMetrics(
            team_id=2,
            team_name="Liverpool",
            form_rating=7.5,
            avg_goals_scored=1.9,
            avg_goals_conceded=0.9,
            last_10_results=[{'result': 'W'} for _ in range(6)] + [{'result': 'L'} for _ in range(4)]
        )
        
        h2h_stats = HeadToHeadStats(
            total_matches=20,
            home_wins=8,
            away_wins=7,
            draws=5,
            avg_total_goals=2.8
        )
        
        # Patch the data fetching methods
        with patch.object(engine, '_get_team_metrics') as mock_metrics:
            with patch.object(engine, '_get_h2h_stats', return_value=h2h_stats):
                with patch.object(engine, '_get_injury_data', return_value=InjuryData()):
                    mock_metrics.side_effect = [home_metrics, away_metrics]
                    
                    result = engine.predict_match(home_team_id=1, away_team_id=2)
                    
                    # Verify comprehensive result
                    assert result.predicted_outcome in ['home', 'draw', 'away']
                    assert result.confidence > 30
                    assert len(result.key_factors) > 0
                    assert len(result.reasoning) > 0
                    assert result.risk_assessment in ['low', 'medium', 'high']
                    assert len(result.most_likely_scores) > 0
                    assert result.over_25_probability > 0.4  # High scoring teams


if __name__ == '__main__':
    pytest.main([__file__, '-v'])