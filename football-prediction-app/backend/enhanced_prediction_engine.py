from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import statistics

logger = logging.getLogger(__name__)

@dataclass
class TeamForm:
    """Recent form data for a team"""
    team_id: int
    team_name: str
    last_5_results: List[str] = field(default_factory=list)  # W/D/L
    goals_scored: int = 0
    goals_conceded: int = 0
    clean_sheets: int = 0
    btts_count: int = 0
    home_record: Dict[str, int] = field(default_factory=lambda: {"W": 0, "D": 0, "L": 0})
    away_record: Dict[str, int] = field(default_factory=lambda: {"W": 0, "D": 0, "L": 0})
    form_rating: float = 0.0  # 0-10 scale

@dataclass
class HeadToHeadStats:
    """Head to head statistics between two teams"""
    total_matches: int = 0
    home_wins: int = 0
    away_wins: int = 0
    draws: int = 0
    total_goals: int = 0
    avg_goals_per_match: float = 0.0
    btts_percentage: float = 0.0
    over_25_percentage: float = 0.0
    recent_results: List[Dict] = field(default_factory=list)

@dataclass
class InjuryReport:
    """Injury and suspension data for a team"""
    team_id: int
    injured_players: List[Dict] = field(default_factory=list)
    suspended_players: List[Dict] = field(default_factory=list)
    key_players_missing: List[str] = field(default_factory=list)
    impact_rating: float = 0.0  # 0-10 scale (10 = severe impact)

@dataclass
class StandingsContext:
    """League standings and motivation context"""
    home_position: int
    away_position: int
    home_points_from_top: int
    away_points_from_top: int
    home_points_from_relegation: int
    away_points_from_relegation: int
    home_motivation: str  # "title_race", "european_spots", "mid_table", "relegation_battle"
    away_motivation: str

@dataclass
class EnhancedPrediction:
    """Enhanced prediction with all factors considered"""
    fixture_id: int
    home_team: str
    away_team: str
    date: str
    win_probability_home: float
    win_probability_away: float
    draw_probability: float
    confidence_level: str  # "high", "medium", "low"
    prediction_factors: Dict[str, float]
    prediction_summary: str
    recommended_bets: List[Dict[str, Any]]
    expected_goals: Dict[str, float]
    btts_probability: float
    over_25_probability: float


class EnhancedPredictionEngine:
    """
    Advanced prediction engine that combines multiple data sources
    with weighted factors for accurate football match predictions
    """
    
    def __init__(self, sportmonks_client):
        self.client = sportmonks_client
        self.weights = {
            'recent_form': 0.40,
            'head_to_head': 0.20,
            'injuries': 0.15,
            'home_advantage': 0.10,
            'standings': 0.10,
            'other_factors': 0.05
        }
        
    def get_enhanced_prediction(self, fixture_id: int) -> Optional[EnhancedPrediction]:
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
            
            # Parallel data fetching for performance
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = {
                    executor.submit(self._get_team_form, home_team_id, True): 'home_form',
                    executor.submit(self._get_team_form, away_team_id, False): 'away_form',
                    executor.submit(self._get_head_to_head_stats, home_team_id, away_team_id): 'h2h',
                    executor.submit(self._get_injury_reports, home_team_id, away_team_id): 'injuries',
                    executor.submit(self._get_standings_context, fixture_data['league_id'], 
                                  home_team_id, away_team_id): 'standings',
                    executor.submit(self._get_sportmonks_predictions, fixture_id): 'base_predictions'
                }
                
                results = {}
                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        results[key] = future.result()
                    except Exception as e:
                        logger.error(f"Error fetching {key}: {str(e)}")
                        results[key] = None
            
            # Calculate weighted prediction
            prediction = self._calculate_weighted_prediction(
                fixture_data=fixture_data,
                home_form=results.get('home_form'),
                away_form=results.get('away_form'),
                h2h_stats=results.get('h2h'),
                injuries=results.get('injuries'),
                standings=results.get('standings'),
                base_predictions=results.get('base_predictions')
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error generating enhanced prediction: {str(e)}")
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
            logger.error(f"Error getting fixture details: {str(e)}")
            return None
    
    def _get_team_form(self, team_id: int, is_home: bool) -> Optional[TeamForm]:
        """Get recent form for a team"""
        try:
            # Get last 10 matches
            today = datetime.utcnow()
            end_date = today.strftime('%Y-%m-%d')
            start_date = (today - timedelta(days=60)).strftime('%Y-%m-%d')
            
            fixtures = self.client.get_fixtures_by_date_range(
                start_date=start_date,
                end_date=end_date,
                team_id=team_id,
                include=['participants', 'scores', 'state']
            )
            
            # Filter finished matches and sort by date
            finished_fixtures = [f for f in fixtures if f.get('state_id') == 4]  # 4 = FT
            finished_fixtures.sort(key=lambda x: x['starting_at'], reverse=True)
            
            # Take last 5 matches
            recent_fixtures = finished_fixtures[:5]
            
            form = TeamForm(team_id=team_id, team_name="")
            
            for fixture in recent_fixtures:
                participants = fixture.get('participants', [])
                home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
                away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
                
                is_team_home = home_team.get('id') == team_id
                
                # Get scores
                scores = fixture.get('scores', [])
                ft_score = next((s for s in scores if s.get('description') == 'CURRENT'), scores[0] if scores else {})
                
                home_goals = ft_score.get('score', {}).get('participant', {}).get('home', 0)
                away_goals = ft_score.get('score', {}).get('participant', {}).get('away', 0)
                
                # Determine result
                if is_team_home:
                    team_goals = home_goals
                    opponent_goals = away_goals
                    form.team_name = home_team.get('name', '')
                else:
                    team_goals = away_goals
                    opponent_goals = home_goals
                    form.team_name = away_team.get('name', '')
                
                # Update form data
                form.goals_scored += team_goals
                form.goals_conceded += opponent_goals
                
                if team_goals > opponent_goals:
                    result = 'W'
                    if is_team_home:
                        form.home_record['W'] += 1
                    else:
                        form.away_record['W'] += 1
                elif team_goals < opponent_goals:
                    result = 'L'
                    if is_team_home:
                        form.home_record['L'] += 1
                    else:
                        form.away_record['L'] += 1
                else:
                    result = 'D'
                    if is_team_home:
                        form.home_record['D'] += 1
                    else:
                        form.away_record['D'] += 1
                
                form.last_5_results.append(result)
                
                if opponent_goals == 0:
                    form.clean_sheets += 1
                if home_goals > 0 and away_goals > 0:
                    form.btts_count += 1
            
            # Calculate form rating
            points = sum(3 if r == 'W' else 1 if r == 'D' else 0 for r in form.last_5_results)
            form.form_rating = (points / 15.0) * 10  # Max 15 points possible, scale to 10
            
            return form
            
        except Exception as e:
            logger.error(f"Error getting team form: {str(e)}")
            return None
    
    def _get_head_to_head_stats(self, home_team_id: int, away_team_id: int) -> Optional[HeadToHeadStats]:
        """Get head to head statistics"""
        try:
            response = self.client.get(
                f'fixtures/head-to-head/{home_team_id}/{away_team_id}',
                params={'include': 'participants;scores;state'}
            )
            
            if not response or 'data' not in response:
                return None
            
            h2h = HeadToHeadStats()
            
            for fixture in response['data'][:10]:  # Last 10 H2H matches
                if fixture.get('state_id') != 4:  # Only finished matches
                    continue
                
                participants = fixture.get('participants', [])
                home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
                away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
                
                # Get scores
                scores = fixture.get('scores', [])
                ft_score = next((s for s in scores if s.get('description') == 'CURRENT'), scores[0] if scores else {})
                
                home_goals = ft_score.get('score', {}).get('participant', {}).get('home', 0)
                away_goals = ft_score.get('score', {}).get('participant', {}).get('away', 0)
                
                h2h.total_matches += 1
                h2h.total_goals += home_goals + away_goals
                
                # Determine winner relative to our fixture's home team
                if home_team.get('id') == home_team_id:
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
                
                if home_goals > 0 and away_goals > 0:
                    h2h.btts_percentage += 1
                if home_goals + away_goals > 2.5:
                    h2h.over_25_percentage += 1
                
                h2h.recent_results.append({
                    'date': fixture.get('starting_at'),
                    'home_team': home_team.get('name'),
                    'away_team': away_team.get('name'),
                    'score': f"{home_goals}-{away_goals}"
                })
            
            if h2h.total_matches > 0:
                h2h.avg_goals_per_match = h2h.total_goals / h2h.total_matches
                h2h.btts_percentage = (h2h.btts_percentage / h2h.total_matches) * 100
                h2h.over_25_percentage = (h2h.over_25_percentage / h2h.total_matches) * 100
            
            return h2h
            
        except Exception as e:
            logger.error(f"Error getting H2H stats: {str(e)}")
            return None
    
    def _get_injury_reports(self, home_team_id: int, away_team_id: int) -> Optional[Dict[str, InjuryReport]]:
        """Get injury and suspension reports for both teams"""
        try:
            reports = {}
            
            for team_id, key in [(home_team_id, 'home'), (away_team_id, 'away')]:
                response = self.client.get(
                    f'injuries/teams/{team_id}',
                    params={'include': 'player'}
                )
                
                if response and 'data' in response:
                    report = InjuryReport(team_id=team_id)
                    
                    for injury in response['data']:
                        player = injury.get('player', {})
                        injury_data = {
                            'player_name': player.get('display_name', 'Unknown'),
                            'position': player.get('position', {}).get('name', 'Unknown'),
                            'reason': injury.get('reason', 'Unknown'),
                            'return_date': injury.get('return_date')
                        }
                        
                        if injury.get('type') == 'injury':
                            report.injured_players.append(injury_data)
                        else:
                            report.suspended_players.append(injury_data)
                        
                        # Check if key player (simplified logic)
                        if player.get('position', {}).get('name') in ['Forward', 'Midfielder'] and \
                           player.get('market_value', 0) > 10000000:
                            report.key_players_missing.append(player.get('display_name'))
                    
                    # Calculate impact rating
                    total_missing = len(report.injured_players) + len(report.suspended_players)
                    key_missing = len(report.key_players_missing)
                    report.impact_rating = min(10, total_missing * 1.5 + key_missing * 3)
                    
                    reports[key] = report
                else:
                    reports[key] = InjuryReport(team_id=team_id)
            
            return reports
            
        except Exception as e:
            logger.error(f"Error getting injury reports: {str(e)}")
            return None
    
    def _get_standings_context(self, league_id: int, home_team_id: int, 
                              away_team_id: int) -> Optional[StandingsContext]:
        """Get league standings and motivation context"""
        try:
            # Get current season
            season_id = self.client.get_current_season_id(league_id)
            if not season_id:
                return None
            
            response = self.client.get_standings(season_id, include=['participant'])
            if not response or 'data' not in response:
                return None
            
            standings = response['data']
            home_standing = next((s for s in standings if s.get('participant_id') == home_team_id), None)
            away_standing = next((s for s in standings if s.get('participant_id') == away_team_id), None)
            
            if not home_standing or not away_standing:
                return None
            
            total_teams = len(standings)
            
            context = StandingsContext(
                home_position=home_standing.get('position', 0),
                away_position=away_standing.get('position', 0),
                home_points_from_top=standings[0].get('points', 0) - home_standing.get('points', 0),
                away_points_from_top=standings[0].get('points', 0) - away_standing.get('points', 0),
                home_points_from_relegation=home_standing.get('points', 0) - standings[-3].get('points', 0),
                away_points_from_relegation=away_standing.get('points', 0) - standings[-3].get('points', 0),
                home_motivation=self._determine_motivation(home_standing.get('position', 0), total_teams),
                away_motivation=self._determine_motivation(away_standing.get('position', 0), total_teams)
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting standings context: {str(e)}")
            return None
    
    def _determine_motivation(self, position: int, total_teams: int) -> str:
        """Determine team motivation based on league position"""
        if position <= 2:
            return "title_race"
        elif position <= 6:
            return "european_spots"
        elif position >= total_teams - 2:
            return "relegation_battle"
        else:
            return "mid_table"
    
    def _get_sportmonks_predictions(self, fixture_id: int) -> Optional[Dict]:
        """Get base predictions from SportMonks"""
        try:
            response = self.client.get_fixture_with_predictions(fixture_id)
            if not response or 'data' not in response:
                return None
            
            predictions_list = response['data'].get('predictions', [])
            
            base_predictions = {
                'match_winner': {'home': 33.33, 'draw': 33.33, 'away': 33.33},
                'btts': {'yes': 50, 'no': 50},
                'over_25': {'yes': 50, 'no': 50}
            }
            
            for pred in predictions_list:
                pred_type = pred.get('type', {}).get('code', '')
                predictions = pred.get('predictions', {})
                
                if pred_type == 'fulltime-result-probability':
                    base_predictions['match_winner'] = {
                        'home': predictions.get('home', 33.33),
                        'draw': predictions.get('draw', 33.33),
                        'away': predictions.get('away', 33.33)
                    }
                elif pred_type == 'both-teams-to-score-probability':
                    base_predictions['btts'] = {
                        'yes': predictions.get('yes', 50),
                        'no': predictions.get('no', 50)
                    }
                elif pred_type == 'over-under-2_5-probability':
                    base_predictions['over_25'] = {
                        'yes': predictions.get('yes', 50),
                        'no': predictions.get('no', 50)
                    }
            
            return base_predictions
            
        except Exception as e:
            logger.error(f"Error getting SportMonks predictions: {str(e)}")
            return None
    
    def _calculate_weighted_prediction(self, fixture_data: Dict, home_form: Optional[TeamForm],
                                     away_form: Optional[TeamForm], h2h_stats: Optional[HeadToHeadStats],
                                     injuries: Optional[Dict], standings: Optional[StandingsContext],
                                     base_predictions: Optional[Dict]) -> EnhancedPrediction:
        """Calculate final weighted prediction based on all factors"""
        
        # Initialize base probabilities
        if base_predictions:
            home_prob = base_predictions['match_winner']['home']
            draw_prob = base_predictions['match_winner']['draw']
            away_prob = base_predictions['match_winner']['away']
            btts_prob = base_predictions['btts']['yes']
            over_25_prob = base_predictions['over_25']['yes']
        else:
            home_prob = 40.0  # Default home advantage
            draw_prob = 28.0
            away_prob = 32.0
            btts_prob = 52.0
            over_25_prob = 51.0
        
        prediction_factors = {}
        adjustments = {'home': 0, 'draw': 0, 'away': 0}
        
        # Factor 1: Recent Form (40%)
        if home_form and away_form:
            form_diff = home_form.form_rating - away_form.form_rating
            form_adjustment = form_diff * 2  # Scale adjustment
            
            if form_diff > 0:
                adjustments['home'] += form_adjustment * self.weights['recent_form']
                adjustments['away'] -= form_adjustment * self.weights['recent_form'] * 0.7
                adjustments['draw'] -= form_adjustment * self.weights['recent_form'] * 0.3
            else:
                adjustments['away'] += abs(form_adjustment) * self.weights['recent_form']
                adjustments['home'] -= abs(form_adjustment) * self.weights['recent_form'] * 0.7
                adjustments['draw'] -= abs(form_adjustment) * self.weights['recent_form'] * 0.3
            
            prediction_factors['form_impact'] = form_diff
            
            # Goal expectations
            home_goals_avg = home_form.goals_scored / len(home_form.last_5_results) if home_form.last_5_results else 1.5
            away_goals_avg = away_form.goals_scored / len(away_form.last_5_results) if away_form.last_5_results else 1.2
            
            # BTTS adjustment
            home_btts_rate = home_form.btts_count / len(home_form.last_5_results) if home_form.last_5_results else 0.5
            away_btts_rate = away_form.btts_count / len(away_form.last_5_results) if away_form.last_5_results else 0.5
            btts_prob = btts_prob * 0.5 + (home_btts_rate + away_btts_rate) * 25
            
            # Over 2.5 adjustment
            total_expected = home_goals_avg + away_goals_avg
            if total_expected > 2.5:
                over_25_prob = min(85, over_25_prob + (total_expected - 2.5) * 15)
            else:
                over_25_prob = max(15, over_25_prob - (2.5 - total_expected) * 15)
        
        # Factor 2: Head to Head (20%)
        if h2h_stats and h2h_stats.total_matches >= 3:
            h2h_home_rate = h2h_stats.home_wins / h2h_stats.total_matches
            h2h_away_rate = h2h_stats.away_wins / h2h_stats.total_matches
            h2h_draw_rate = h2h_stats.draws / h2h_stats.total_matches
            
            adjustments['home'] += (h2h_home_rate - 0.4) * 20 * self.weights['head_to_head']
            adjustments['away'] += (h2h_away_rate - 0.3) * 20 * self.weights['head_to_head']
            adjustments['draw'] += (h2h_draw_rate - 0.3) * 20 * self.weights['head_to_head']
            
            prediction_factors['h2h_pattern'] = f"H{h2h_stats.home_wins}-D{h2h_stats.draws}-A{h2h_stats.away_wins}"
            
            # Historical goal patterns
            btts_prob = btts_prob * 0.7 + h2h_stats.btts_percentage * 0.3
            over_25_prob = over_25_prob * 0.7 + h2h_stats.over_25_percentage * 0.3
        
        # Factor 3: Injuries (15%)
        if injuries:
            home_injury = injuries.get('home', InjuryReport(team_id=fixture_data['home_team_id']))
            away_injury = injuries.get('away', InjuryReport(team_id=fixture_data['away_team_id']))
            
            injury_diff = away_injury.impact_rating - home_injury.impact_rating
            
            if injury_diff > 0:  # Away team more affected
                adjustments['home'] += injury_diff * self.weights['injuries']
                adjustments['away'] -= injury_diff * self.weights['injuries']
            else:  # Home team more affected
                adjustments['away'] += abs(injury_diff) * self.weights['injuries']
                adjustments['home'] -= abs(injury_diff) * self.weights['injuries']
            
            prediction_factors['injury_impact'] = injury_diff
        
        # Factor 4: Home Advantage (10%)
        adjustments['home'] += 5 * self.weights['home_advantage']
        adjustments['away'] -= 3 * self.weights['home_advantage']
        adjustments['draw'] -= 2 * self.weights['home_advantage']
        
        # Factor 5: League Standing & Motivation (10%)
        if standings:
            motivation_values = {
                'title_race': 3,
                'european_spots': 2,
                'relegation_battle': 2.5,
                'mid_table': 0
            }
            
            home_motivation = motivation_values.get(standings.home_motivation, 0)
            away_motivation = motivation_values.get(standings.away_motivation, 0)
            
            motivation_diff = home_motivation - away_motivation
            
            if motivation_diff > 0:
                adjustments['home'] += motivation_diff * self.weights['standings']
                adjustments['away'] -= motivation_diff * self.weights['standings'] * 0.7
            else:
                adjustments['away'] += abs(motivation_diff) * self.weights['standings']
                adjustments['home'] -= abs(motivation_diff) * self.weights['standings'] * 0.7
            
            prediction_factors['motivation'] = f"H:{standings.home_motivation}, A:{standings.away_motivation}"
        
        # Apply adjustments
        home_prob += adjustments['home']
        draw_prob += adjustments['draw']
        away_prob += adjustments['away']
        
        # Normalize probabilities
        total = home_prob + draw_prob + away_prob
        home_prob = round((home_prob / total) * 100, 2)
        draw_prob = round((draw_prob / total) * 100, 2)
        away_prob = round((away_prob / total) * 100, 2)
        
        # Ensure they sum to 100
        diff = 100 - (home_prob + draw_prob + away_prob)
        home_prob += diff
        
        # Determine confidence level
        max_prob = max(home_prob, draw_prob, away_prob)
        if max_prob > 55:
            confidence = "high"
        elif max_prob > 45:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Generate prediction summary
        prediction_summary = self._generate_prediction_summary(
            fixture_data, home_prob, draw_prob, away_prob,
            home_form, away_form, h2h_stats, injuries, standings
        )
        
        # Generate recommended bets
        recommended_bets = self._generate_bet_recommendations(
            home_prob, draw_prob, away_prob, btts_prob, over_25_prob,
            home_form, away_form
        )
        
        # Expected goals calculation
        expected_goals = {
            'home': round(home_goals_avg if home_form else 1.3, 2),
            'away': round(away_goals_avg if away_form else 1.1, 2)
        }
        
        return EnhancedPrediction(
            fixture_id=fixture_data['fixture_id'],
            home_team=fixture_data['home_team_name'],
            away_team=fixture_data['away_team_name'],
            date=fixture_data['date'],
            win_probability_home=home_prob,
            win_probability_away=away_prob,
            draw_probability=draw_prob,
            confidence_level=confidence,
            prediction_factors=prediction_factors,
            prediction_summary=prediction_summary,
            recommended_bets=recommended_bets,
            expected_goals=expected_goals,
            btts_probability=round(btts_prob, 2),
            over_25_probability=round(over_25_prob, 2)
        )
    
    def _generate_prediction_summary(self, fixture_data: Dict, home_prob: float, draw_prob: float,
                                   away_prob: float, home_form: Optional[TeamForm],
                                   away_form: Optional[TeamForm], h2h_stats: Optional[HeadToHeadStats],
                                   injuries: Optional[Dict], standings: Optional[StandingsContext]) -> str:
        """Generate human-readable prediction summary"""
        
        summary_parts = []
        
        # Main prediction
        if home_prob > away_prob and home_prob > draw_prob:
            summary_parts.append(f"{fixture_data['home_team_name']} is predicted to win with {home_prob}% probability.")
        elif away_prob > home_prob and away_prob > draw_prob:
            summary_parts.append(f"{fixture_data['away_team_name']} is predicted to win with {away_prob}% probability.")
        else:
            summary_parts.append(f"A draw is the most likely outcome with {draw_prob}% probability.")
        
        # Form analysis
        if home_form and away_form:
            if home_form.form_rating > away_form.form_rating + 2:
                summary_parts.append(f"{fixture_data['home_team_name']} is in significantly better form.")
            elif away_form.form_rating > home_form.form_rating + 2:
                summary_parts.append(f"{fixture_data['away_team_name']} is in significantly better form.")
            
            # Recent results
            home_recent = ''.join(home_form.last_5_results[:3])
            away_recent = ''.join(away_form.last_5_results[:3])
            summary_parts.append(f"Recent form: {fixture_data['home_team_name']} ({home_recent}) vs {fixture_data['away_team_name']} ({away_recent}).")
        
        # H2H insight
        if h2h_stats and h2h_stats.total_matches >= 3:
            if h2h_stats.home_wins > h2h_stats.away_wins:
                summary_parts.append(f"{fixture_data['home_team_name']} has dominated recent H2H meetings ({h2h_stats.home_wins} wins in {h2h_stats.total_matches} games).")
            elif h2h_stats.away_wins > h2h_stats.home_wins:
                summary_parts.append(f"{fixture_data['away_team_name']} has a strong H2H record ({h2h_stats.away_wins} wins in {h2h_stats.total_matches} games).")
            
            if h2h_stats.avg_goals_per_match > 3:
                summary_parts.append("H2H matches tend to be high-scoring.")
            elif h2h_stats.avg_goals_per_match < 2:
                summary_parts.append("H2H matches are typically low-scoring affairs.")
        
        # Injury impact
        if injuries:
            home_injury = injuries.get('home')
            away_injury = injuries.get('away')
            
            if home_injury and home_injury.key_players_missing:
                summary_parts.append(f"{fixture_data['home_team_name']} missing key players: {', '.join(home_injury.key_players_missing[:2])}.")
            if away_injury and away_injury.key_players_missing:
                summary_parts.append(f"{fixture_data['away_team_name']} missing key players: {', '.join(away_injury.key_players_missing[:2])}.")
        
        # Motivation
        if standings:
            if standings.home_motivation == "title_race":
                summary_parts.append(f"{fixture_data['home_team_name']} fighting for the title.")
            elif standings.home_motivation == "relegation_battle":
                summary_parts.append(f"{fixture_data['home_team_name']} battling relegation.")
            
            if standings.away_motivation == "title_race":
                summary_parts.append(f"{fixture_data['away_team_name']} fighting for the title.")
            elif standings.away_motivation == "relegation_battle":
                summary_parts.append(f"{fixture_data['away_team_name']} battling relegation.")
        
        return " ".join(summary_parts[:5])  # Limit to 5 key points
    
    def _generate_bet_recommendations(self, home_prob: float, draw_prob: float, away_prob: float,
                                     btts_prob: float, over_25_prob: float,
                                     home_form: Optional[TeamForm], away_form: Optional[TeamForm]) -> List[Dict]:
        """Generate betting recommendations based on probabilities"""
        
        recommendations = []
        
        # Match result recommendations
        if home_prob > 55:
            recommendations.append({
                'type': 'Match Result',
                'selection': 'Home Win',
                'probability': home_prob,
                'confidence': 'high' if home_prob > 65 else 'medium',
                'reasoning': 'Strong home advantage and form'
            })
        elif away_prob > 55:
            recommendations.append({
                'type': 'Match Result',
                'selection': 'Away Win',
                'probability': away_prob,
                'confidence': 'high' if away_prob > 65 else 'medium',
                'reasoning': 'Away team in superior form'
            })
        
        # Double chance
        home_or_draw = home_prob + draw_prob
        away_or_draw = away_prob + draw_prob
        
        if home_or_draw > 70:
            recommendations.append({
                'type': 'Double Chance',
                'selection': 'Home or Draw',
                'probability': home_or_draw,
                'confidence': 'high',
                'reasoning': 'Low risk option with high probability'
            })
        elif away_or_draw > 70:
            recommendations.append({
                'type': 'Double Chance',
                'selection': 'Away or Draw',
                'probability': away_or_draw,
                'confidence': 'high',
                'reasoning': 'Low risk option with high probability'
            })
        
        # Goals markets
        if over_25_prob > 65:
            recommendations.append({
                'type': 'Total Goals',
                'selection': 'Over 2.5 Goals',
                'probability': over_25_prob,
                'confidence': 'high' if over_25_prob > 75 else 'medium',
                'reasoning': 'Both teams scoring frequently'
            })
        elif over_25_prob < 35:
            recommendations.append({
                'type': 'Total Goals',
                'selection': 'Under 2.5 Goals',
                'probability': 100 - over_25_prob,
                'confidence': 'high' if (100 - over_25_prob) > 75 else 'medium',
                'reasoning': 'Defensive teams or poor attacking form'
            })
        
        # BTTS
        if btts_prob > 65:
            recommendations.append({
                'type': 'Both Teams to Score',
                'selection': 'Yes',
                'probability': btts_prob,
                'confidence': 'high' if btts_prob > 75 else 'medium',
                'reasoning': 'Both teams have been finding the net regularly'
            })
        elif btts_prob < 35:
            recommendations.append({
                'type': 'Both Teams to Score',
                'selection': 'No',
                'probability': 100 - btts_prob,
                'confidence': 'high' if (100 - btts_prob) > 75 else 'medium',
                'reasoning': 'One or both teams struggling to score'
            })
        
        # Sort by confidence and probability
        recommendations.sort(key=lambda x: (
            {'high': 3, 'medium': 2, 'low': 1}[x['confidence']],
            x['probability']
        ), reverse=True)
        
        return recommendations[:4]  # Return top 4 recommendations