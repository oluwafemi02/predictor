import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
import lightgbm as lgb
from datetime import datetime, timedelta
import joblib
import logging
from typing import Dict, List, Tuple, Optional
from models import db, Match, Team, TeamStatistics, HeadToHead, Injury, Player, PlayerPerformance, Prediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FootballPredictionModel:
    def __init__(self):
        self.models = {
            'xgboost': None,
            'lightgbm': None,
            'random_forest': None,
            'gradient_boosting': None,
            'ensemble': None
        }
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
    
    def extract_features(self, match: Match) -> Dict[str, float]:
        """Extract features for a single match"""
        features = {}
        
        # Get team statistics
        home_team = Team.query.get(match.home_team_id)
        away_team = Team.query.get(match.away_team_id)
        
        # Get current season statistics
        home_stats = TeamStatistics.query.filter_by(
            team_id=match.home_team_id,
            season=match.season
        ).first()
        away_stats = TeamStatistics.query.filter_by(
            team_id=match.away_team_id,
            season=match.season
        ).first()
        
        if not home_stats or not away_stats:
            return None
        
        # Basic team performance features
        features['home_win_rate'] = home_stats.wins / max(home_stats.matches_played, 1)
        features['away_win_rate'] = away_stats.wins / max(away_stats.matches_played, 1)
        features['home_draw_rate'] = home_stats.draws / max(home_stats.matches_played, 1)
        features['away_draw_rate'] = away_stats.draws / max(away_stats.matches_played, 1)
        
        # Goal statistics
        features['home_goals_per_match'] = home_stats.goals_for / max(home_stats.matches_played, 1)
        features['away_goals_per_match'] = away_stats.goals_for / max(away_stats.matches_played, 1)
        features['home_goals_conceded_per_match'] = home_stats.goals_against / max(home_stats.matches_played, 1)
        features['away_goals_conceded_per_match'] = away_stats.goals_against / max(away_stats.matches_played, 1)
        
        # Home/Away specific performance
        features['home_team_home_win_rate'] = home_stats.home_wins / max(home_stats.home_wins + home_stats.home_draws + home_stats.home_losses, 1)
        features['away_team_away_win_rate'] = away_stats.away_wins / max(away_stats.away_wins + away_stats.away_draws + away_stats.away_losses, 1)
        
        # Form (convert to numeric)
        features['home_form_score'] = self._calculate_form_score(home_stats.form)
        features['away_form_score'] = self._calculate_form_score(away_stats.form)
        
        # Head-to-head statistics
        h2h = self._get_head_to_head(match.home_team_id, match.away_team_id)
        if h2h:
            total_h2h_matches = max(h2h.total_matches, 1)
            if h2h.team1_id == match.home_team_id:
                features['h2h_home_win_rate'] = h2h.team1_wins / total_h2h_matches
                features['h2h_away_win_rate'] = h2h.team2_wins / total_h2h_matches
                features['h2h_home_goals_avg'] = h2h.team1_goals / total_h2h_matches
                features['h2h_away_goals_avg'] = h2h.team2_goals / total_h2h_matches
            else:
                features['h2h_home_win_rate'] = h2h.team2_wins / total_h2h_matches
                features['h2h_away_win_rate'] = h2h.team1_wins / total_h2h_matches
                features['h2h_home_goals_avg'] = h2h.team2_goals / total_h2h_matches
                features['h2h_away_goals_avg'] = h2h.team1_goals / total_h2h_matches
            features['h2h_draw_rate'] = h2h.draws / total_h2h_matches
        else:
            features['h2h_home_win_rate'] = 0.33
            features['h2h_away_win_rate'] = 0.33
            features['h2h_draw_rate'] = 0.34
            features['h2h_home_goals_avg'] = features['home_goals_per_match']
            features['h2h_away_goals_avg'] = features['away_goals_per_match']
        
        # Recent performance (last 5 matches)
        features['home_recent_goals'] = self._get_recent_goals(match.home_team_id, 5)
        features['away_recent_goals'] = self._get_recent_goals(match.away_team_id, 5)
        
        # Injury impact
        features['home_injury_impact'] = self._calculate_injury_impact(match.home_team_id)
        features['away_injury_impact'] = self._calculate_injury_impact(match.away_team_id)
        
        # Days since last match (fatigue factor)
        features['home_days_since_last'] = self._days_since_last_match(match.home_team_id, match.match_date)
        features['away_days_since_last'] = self._days_since_last_match(match.away_team_id, match.match_date)
        
        # Advanced statistics if available
        if home_stats.possession_avg and away_stats.possession_avg:
            features['home_possession_avg'] = home_stats.possession_avg
            features['away_possession_avg'] = away_stats.possession_avg
            features['home_shots_per_game'] = home_stats.shots_per_game or 0
            features['away_shots_per_game'] = away_stats.shots_per_game or 0
            features['home_pass_accuracy'] = home_stats.pass_accuracy or 0
            features['away_pass_accuracy'] = away_stats.pass_accuracy or 0
        
        # Clean sheets
        features['home_clean_sheet_rate'] = home_stats.clean_sheets / max(home_stats.matches_played, 1)
        features['away_clean_sheet_rate'] = away_stats.clean_sheets / max(away_stats.matches_played, 1)
        
        return features
    
    def _calculate_form_score(self, form: str) -> float:
        """Convert form string (e.g., 'WWDLW') to numeric score"""
        if not form:
            return 0.5
        
        score = 0
        weights = [1.0, 0.9, 0.8, 0.7, 0.6]  # Recent matches weighted more
        
        for i, result in enumerate(form[:5]):
            if result == 'W':
                score += 3 * weights[i]
            elif result == 'D':
                score += 1 * weights[i]
        
        return score / (sum(weights[:len(form)]) * 3)  # Normalize to 0-1
    
    def _get_head_to_head(self, team1_id: int, team2_id: int) -> Optional[HeadToHead]:
        """Get head-to-head record between two teams"""
        if team1_id > team2_id:
            team1_id, team2_id = team2_id, team1_id
        return HeadToHead.query.filter_by(team1_id=team1_id, team2_id=team2_id).first()
    
    def _get_recent_goals(self, team_id: int, num_matches: int) -> float:
        """Get average goals scored in recent matches"""
        recent_matches = Match.query.filter(
            db.or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.status == 'finished'
        ).order_by(Match.match_date.desc()).limit(num_matches).all()
        
        if not recent_matches:
            return 0
        
        total_goals = 0
        for match in recent_matches:
            if match.home_team_id == team_id:
                total_goals += match.home_score or 0
            else:
                total_goals += match.away_score or 0
        
        return total_goals / len(recent_matches)
    
    def _calculate_injury_impact(self, team_id: int) -> float:
        """Calculate the impact of injuries on team performance"""
        # Get active injuries
        active_injuries = Injury.query.join(Player).filter(
            Player.team_id == team_id,
            Injury.status == 'active'
        ).all()
        
        if not active_injuries:
            return 0
        
        impact = 0
        for injury in active_injuries:
            player = injury.player
            # Weight by player importance (simplified - could use actual performance data)
            if player.position in ['Forward', 'Striker']:
                impact += 0.3
            elif player.position in ['Midfielder', 'Winger']:
                impact += 0.2
            elif player.position in ['Defender']:
                impact += 0.15
            elif player.position == 'Goalkeeper':
                impact += 0.4
            
            # Adjust by injury severity
            if injury.severity == 'severe':
                impact *= 1.5
            elif injury.severity == 'minor':
                impact *= 0.5
        
        return min(impact, 1.0)  # Cap at 1.0
    
    def _days_since_last_match(self, team_id: int, current_date: datetime) -> int:
        """Calculate days since team's last match"""
        last_match = Match.query.filter(
            db.or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.match_date < current_date,
            Match.status == 'finished'
        ).order_by(Match.match_date.desc()).first()
        
        if not last_match:
            return 7  # Default to a week
        
        return (current_date - last_match.match_date).days
    
    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from historical matches"""
        # Get all finished matches with sufficient data
        matches = Match.query.filter(
            Match.status == 'finished',
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).order_by(Match.match_date).all()
        
        X = []
        y = []
        
        for match in matches:
            features = self.extract_features(match)
            if features:
                X.append(list(features.values()))
                
                # Create target: 0 = home win, 1 = draw, 2 = away win
                if match.home_score > match.away_score:
                    y.append(0)
                elif match.home_score == match.away_score:
                    y.append(1)
                else:
                    y.append(2)
                
                if not self.feature_names:
                    self.feature_names = list(features.keys())
        
        return np.array(X), np.array(y)
    
    def train(self):
        """Train all prediction models"""
        logger.info("Starting model training...")
        
        X, y = self.prepare_training_data()
        
        if len(X) < 100:
            logger.warning("Insufficient data for training. Need at least 100 matches.")
            return
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train XGBoost
        self.models['xgboost'] = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            objective='multi:softprob',
            random_state=42
        )
        self.models['xgboost'].fit(X_train_scaled, y_train)
        
        # Train LightGBM
        self.models['lightgbm'] = lgb.LGBMClassifier(
            n_estimators=200,
            num_leaves=31,
            learning_rate=0.1,
            objective='multiclass',
            num_class=3,
            random_state=42
        )
        self.models['lightgbm'].fit(X_train_scaled, y_train)
        
        # Train Random Forest
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            random_state=42
        )
        self.models['random_forest'].fit(X_train_scaled, y_train)
        
        # Train Gradient Boosting
        self.models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.models['gradient_boosting'].fit(X_train_scaled, y_train)
        
        # Evaluate models
        for name, model in self.models.items():
            if model:
                y_pred = model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                logger.info(f"{name} accuracy: {accuracy:.3f}")
        
        self.is_trained = True
        logger.info("Model training completed")
    
    def predict_match(self, match: Match) -> Dict:
        """Predict the outcome of a match"""
        if not self.is_trained:
            logger.error("Model not trained yet")
            return None
        
        features = self.extract_features(match)
        if not features:
            logger.error("Could not extract features for match")
            return None
        
        X = np.array([list(features.values())])
        X_scaled = self.scaler.transform(X)
        
        # Get predictions from all models
        predictions = {}
        probabilities = []
        
        for name, model in self.models.items():
            if model:
                proba = model.predict_proba(X_scaled)[0]
                predictions[name] = {
                    'home_win': float(proba[0]),
                    'draw': float(proba[1]),
                    'away_win': float(proba[2])
                }
                probabilities.append(proba)
        
        # Ensemble prediction (average)
        ensemble_proba = np.mean(probabilities, axis=0)
        
        # Calculate expected goals using regression
        home_expected_goals = self._predict_goals(features, 'home')
        away_expected_goals = self._predict_goals(features, 'away')
        
        # Prepare prediction result
        result = {
            'match_id': match.id,
            'home_team': match.home_team.name,
            'away_team': match.away_team.name,
            'match_date': match.match_date.isoformat(),
            'predictions': {
                'ensemble': {
                    'home_win_probability': float(ensemble_proba[0]),
                    'draw_probability': float(ensemble_proba[1]),
                    'away_win_probability': float(ensemble_proba[2])
                },
                'individual_models': predictions
            },
            'expected_goals': {
                'home': float(home_expected_goals),
                'away': float(away_expected_goals)
            },
            'most_likely_result': self._get_most_likely_result(ensemble_proba),
            'confidence': float(np.max(ensemble_proba)),
            'betting_suggestions': self._generate_betting_suggestions(ensemble_proba, home_expected_goals, away_expected_goals),
            'factors': self._explain_prediction(features, ensemble_proba)
        }
        
        # Save prediction to database
        self._save_prediction(match, result)
        
        return result
    
    def _predict_goals(self, features: Dict, team: str) -> float:
        """Predict expected goals for a team"""
        # Simplified goal prediction based on features
        if team == 'home':
            base_goals = features.get('home_goals_per_match', 1.5)
            opponent_defense = features.get('away_goals_conceded_per_match', 1.5)
            form_factor = features.get('home_form_score', 0.5)
            h2h_goals = features.get('h2h_home_goals_avg', base_goals)
        else:
            base_goals = features.get('away_goals_per_match', 1.5)
            opponent_defense = features.get('home_goals_conceded_per_match', 1.5)
            form_factor = features.get('away_form_score', 0.5)
            h2h_goals = features.get('h2h_away_goals_avg', base_goals)
        
        # Weighted calculation
        expected_goals = (
            0.3 * base_goals +
            0.2 * opponent_defense +
            0.2 * (form_factor * 3) +  # Form affects scoring
            0.2 * h2h_goals +
            0.1 * features.get(f'{team}_recent_goals', base_goals)
        )
        
        # Adjust for injuries
        injury_impact = features.get(f'{team}_injury_impact', 0)
        expected_goals *= (1 - injury_impact * 0.3)
        
        return max(0, expected_goals)
    
    def _get_most_likely_result(self, probabilities: np.ndarray) -> str:
        """Get the most likely match result"""
        outcomes = ['Home Win', 'Draw', 'Away Win']
        return outcomes[np.argmax(probabilities)]
    
    def _generate_betting_suggestions(self, probabilities: np.ndarray, home_goals: float, away_goals: float) -> Dict:
        """Generate betting suggestions based on predictions"""
        total_goals = home_goals + away_goals
        
        suggestions = {
            'match_result': {
                'suggestion': self._get_most_likely_result(probabilities),
                'confidence': float(np.max(probabilities))
            },
            'over_under_2.5': {
                'suggestion': 'Over 2.5' if total_goals > 2.5 else 'Under 2.5',
                'probability': float(self._calculate_over_under_probability(total_goals, 2.5))
            },
            'both_teams_to_score': {
                'suggestion': 'Yes' if home_goals > 0.8 and away_goals > 0.8 else 'No',
                'probability': float(min(home_goals, away_goals) / 1.5)  # Simplified
            },
            'correct_score': {
                'suggestion': f"{round(home_goals)}-{round(away_goals)}",
                'confidence': 'Low'  # Correct score is always low confidence
            }
        }
        
        # Add value bets (simplified - would need actual odds for proper calculation)
        if probabilities[0] > 0.6:  # Strong home win probability
            suggestions['value_bet'] = 'Home Win'
        elif probabilities[2] > 0.6:  # Strong away win probability
            suggestions['value_bet'] = 'Away Win'
        elif probabilities[1] > 0.4:  # High draw probability
            suggestions['value_bet'] = 'Draw'
        
        return suggestions
    
    def _calculate_over_under_probability(self, expected_goals: float, threshold: float) -> float:
        """Calculate probability of total goals being over/under threshold"""
        # Using Poisson distribution approximation
        from scipy.stats import poisson
        
        # Sum of two Poisson distributions
        prob_under = sum(poisson.pmf(i, expected_goals) for i in range(int(threshold) + 1))
        return 1 - prob_under
    
    def _explain_prediction(self, features: Dict, probabilities: np.ndarray) -> Dict:
        """Explain key factors influencing the prediction"""
        factors = {}
        
        # Identify strongest factors
        if features['home_form_score'] > features['away_form_score']:
            factors['form'] = f"Home team in better recent form ({features['home_form_score']:.2f} vs {features['away_form_score']:.2f})"
        elif features['away_form_score'] > features['home_form_score']:
            factors['form'] = f"Away team in better recent form ({features['away_form_score']:.2f} vs {features['home_form_score']:.2f})"
        
        if features['h2h_home_win_rate'] > 0.6:
            factors['head_to_head'] = "Home team dominates historical matchups"
        elif features['h2h_away_win_rate'] > 0.6:
            factors['head_to_head'] = "Away team dominates historical matchups"
        
        if features['home_injury_impact'] > 0.3:
            factors['injuries'] = "Home team affected by key player injuries"
        if features['away_injury_impact'] > 0.3:
            factors['injuries'] = "Away team affected by key player injuries"
        
        if features['home_team_home_win_rate'] > 0.7:
            factors['home_advantage'] = "Strong home record for home team"
        
        if features['home_days_since_last'] < 3 or features['away_days_since_last'] < 3:
            factors['fatigue'] = "Potential fatigue factor due to recent matches"
        
        return factors
    
    def _save_prediction(self, match: Match, result: Dict):
        """Save prediction to database"""
        prediction = Prediction(
            match_id=match.id,
            home_win_probability=result['predictions']['ensemble']['home_win_probability'],
            draw_probability=result['predictions']['ensemble']['draw_probability'],
            away_win_probability=result['predictions']['ensemble']['away_win_probability'],
            predicted_home_score=result['expected_goals']['home'],
            predicted_away_score=result['expected_goals']['away'],
            over_2_5_probability=result['betting_suggestions']['over_under_2.5']['probability'],
            both_teams_score_probability=result['betting_suggestions']['both_teams_to_score']['probability'],
            model_version='ensemble_v1',
            confidence_score=result['confidence'],
            factors=result['factors']
        )
        db.session.add(prediction)
        db.session.commit()
    
    def save_model(self, filepath: str = 'models/football_prediction_model.pkl'):
        """Save trained model to file"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str = 'models/football_prediction_model.pkl'):
        """Load trained model from file"""
        try:
            model_data = joblib.load(filepath)
            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.is_trained = model_data['is_trained']
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")