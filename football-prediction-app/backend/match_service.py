"""
Match Service Module
Handles all match-related business logic and database operations
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from models import db, Match, Team, Prediction, TeamStatistics, MatchOdds
from db_utils import DatabaseOptimizer
import logging

logger = logging.getLogger(__name__)


class MatchService:
    """Service class for match-related operations"""
    
    @staticmethod
    def get_match_with_details(match_id: int) -> Optional[Match]:
        """
        Get match with all related data pre-loaded
        
        Args:
            match_id: ID of the match
            
        Returns:
            Match object with relationships loaded or None
        """
        return Match.query.options(
            db.joinedload(Match.home_team),
            db.joinedload(Match.away_team),
            db.selectinload(Match.predictions),
            db.selectinload(Match.odds)
        ).get(match_id)
    
    @staticmethod
    def calculate_head_to_head(
        home_team_id: int, 
        away_team_id: int, 
        match_id: int,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Calculate head-to-head statistics between two teams
        
        Args:
            home_team_id: ID of home team
            away_team_id: ID of away team
            match_id: Current match ID to exclude
            limit: Maximum number of matches to analyze
            
        Returns:
            Dictionary with H2H statistics
        """
        # Get H2H matches efficiently
        h2h_matches = DatabaseOptimizer.optimize_head_to_head_query(
            home_team_id, 
            away_team_id, 
            limit
        )
        
        # Filter out current match
        h2h_matches = [m for m in h2h_matches if m.id != match_id]
        
        # Calculate statistics
        stats = {
            'total_matches': len(h2h_matches),
            'home_wins': 0,
            'away_wins': 0,
            'draws': 0,
            'home_goals': 0,
            'away_goals': 0,
            'last_5_results': []
        }
        
        for match in h2h_matches[:5]:  # Last 5 for results list
            # Determine perspective (which team was home in this match)
            if match.home_team_id == home_team_id:
                home_score = match.home_score
                away_score = match.away_score
                result_for_home = 'W' if home_score > away_score else ('D' if home_score == away_score else 'L')
            else:
                home_score = match.away_score
                away_score = match.home_score
                result_for_home = 'W' if home_score > away_score else ('D' if home_score == away_score else 'L')
            
            stats['last_5_results'].append({
                'date': match.match_date.isoformat(),
                'result': result_for_home,
                'score': f"{home_score}-{away_score}"
            })
        
        # Calculate wins/draws/losses from all matches
        for match in h2h_matches:
            if match.home_team_id == home_team_id:
                stats['home_goals'] += match.home_score or 0
                stats['away_goals'] += match.away_score or 0
                
                if match.home_score > match.away_score:
                    stats['home_wins'] += 1
                elif match.away_score > match.home_score:
                    stats['away_wins'] += 1
                else:
                    stats['draws'] += 1
            else:
                stats['home_goals'] += match.away_score or 0
                stats['away_goals'] += match.home_score or 0
                
                if match.away_score > match.home_score:
                    stats['home_wins'] += 1
                elif match.home_score > match.away_score:
                    stats['away_wins'] += 1
                else:
                    stats['draws'] += 1
        
        return stats
    
    @staticmethod
    def get_team_form(team_id: int, venue: str = 'all', limit: int = 5) -> Dict[str, Any]:
        """
        Get team's recent form
        
        Args:
            team_id: Team ID
            venue: 'home', 'away', or 'all'
            limit: Number of matches to analyze
            
        Returns:
            Dictionary with form statistics
        """
        # Build query based on venue
        query = Match.query.filter(
            Match.status == 'finished'
        )
        
        if venue == 'home':
            query = query.filter(Match.home_team_id == team_id)
        elif venue == 'away':
            query = query.filter(Match.away_team_id == team_id)
        else:
            query = query.filter(
                or_(
                    Match.home_team_id == team_id,
                    Match.away_team_id == team_id
                )
            )
        
        # Get recent matches
        recent_matches = query.order_by(
            Match.match_date.desc()
        ).limit(limit).all()
        
        # Calculate form
        form_string = ""
        wins = draws = losses = 0
        goals_for = goals_against = 0
        
        for match in recent_matches:
            if match.home_team_id == team_id:
                gf = match.home_score or 0
                ga = match.away_score or 0
                
                if gf > ga:
                    form_string += "W"
                    wins += 1
                elif gf == ga:
                    form_string += "D"
                    draws += 1
                else:
                    form_string += "L"
                    losses += 1
            else:
                gf = match.away_score or 0
                ga = match.home_score or 0
                
                if gf > ga:
                    form_string += "W"
                    wins += 1
                elif gf == ga:
                    form_string += "D"
                    draws += 1
                else:
                    form_string += "L"
                    losses += 1
            
            goals_for += gf
            goals_against += ga
        
        matches_played = len(recent_matches)
        
        return {
            'form': form_string,
            'recent_matches': matches_played,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'goals_per_match': goals_for / matches_played if matches_played > 0 else 0,
            'goals_conceded_per_match': goals_against / matches_played if matches_played > 0 else 0,
            'points': (wins * 3) + draws,
            'win_percentage': (wins / matches_played * 100) if matches_played > 0 else 0
        }
    
    @staticmethod
    def get_upcoming_matches(
        days_ahead: int = 7,
        team_id: Optional[int] = None,
        competition: Optional[str] = None,
        limit: int = 50
    ) -> List[Match]:
        """
        Get upcoming matches with filters
        
        Args:
            days_ahead: Number of days to look ahead
            team_id: Filter by team (optional)
            competition: Filter by competition (optional)
            limit: Maximum matches to return
            
        Returns:
            List of upcoming matches
        """
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)
        
        query = Match.query.options(
            db.joinedload(Match.home_team),
            db.joinedload(Match.away_team)
        ).filter(
            Match.match_date >= now,
            Match.match_date <= end_date,
            Match.status.in_(['scheduled', 'not_started'])
        )
        
        if team_id:
            query = query.filter(
                or_(
                    Match.home_team_id == team_id,
                    Match.away_team_id == team_id
                )
            )
        
        if competition:
            query = query.filter(Match.competition == competition)
        
        return query.order_by(Match.match_date).limit(limit).all()
    
    @staticmethod
    def get_live_matches() -> List[Match]:
        """
        Get currently live matches
        
        Returns:
            List of live matches
        """
        return Match.query.options(
            db.joinedload(Match.home_team),
            db.joinedload(Match.away_team)
        ).filter(
            Match.status == 'in_play'
        ).order_by(Match.match_date).all()
    
    @staticmethod
    def search_matches(
        search_term: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Match]:
        """
        Search matches by team names or competition
        
        Args:
            search_term: Search string
            date_from: Start date filter
            date_to: End date filter
            status: Match status filter
            limit: Maximum results
            
        Returns:
            List of matching matches
        """
        # Join with teams for searching
        query = Match.query.join(
            Team, Match.home_team_id == Team.id
        ).join(
            Team, Match.away_team_id == Team.id, isouter=True
        ).options(
            db.joinedload(Match.home_team),
            db.joinedload(Match.away_team)
        )
        
        # Apply search filter
        search_pattern = f"%{search_term}%"
        query = query.filter(
            or_(
                Match.competition.ilike(search_pattern),
                Team.name.ilike(search_pattern)
            )
        )
        
        # Apply date filters
        if date_from:
            query = query.filter(Match.match_date >= date_from)
        if date_to:
            query = query.filter(Match.match_date <= date_to)
        
        # Apply status filter
        if status:
            query = query.filter(Match.status == status)
        
        return query.order_by(Match.match_date.desc()).limit(limit).all()
    
    @staticmethod
    def get_match_odds(match_id: int) -> List[MatchOdds]:
        """
        Get all odds for a match
        
        Args:
            match_id: Match ID
            
        Returns:
            List of odds from different bookmakers
        """
        return MatchOdds.query.filter_by(
            match_id=match_id
        ).order_by(
            MatchOdds.bookmaker_name,
            MatchOdds.updated_at.desc()
        ).all()
    
    @staticmethod
    def calculate_match_statistics(match: Match) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for a match
        
        Args:
            match: Match object
            
        Returns:
            Dictionary with match statistics
        """
        stats = {
            'match_id': match.id,
            'date': match.match_date.isoformat() if match.match_date else None,
            'venue': match.venue,
            'competition': match.competition,
            'status': match.status,
            'attendance': match.attendance,
            'referee': match.referee
        }
        
        # Add scores if match is played
        if match.status == 'finished':
            stats.update({
                'home_score': match.home_score,
                'away_score': match.away_score,
                'home_score_halftime': match.home_score_halftime,
                'away_score_halftime': match.away_score_halftime,
                'total_goals': (match.home_score or 0) + (match.away_score or 0),
                'goals_difference': abs((match.home_score or 0) - (match.away_score or 0))
            })
        
        # Add team information
        if match.home_team:
            stats['home_team'] = {
                'id': match.home_team.id,
                'name': match.home_team.name,
                'logo_url': match.home_team.logo_url
            }
        
        if match.away_team:
            stats['away_team'] = {
                'id': match.away_team.id,
                'name': match.away_team.name,
                'logo_url': match.away_team.logo_url
            }
        
        # Add prediction if exists
        if match.predictions:
            latest_prediction = match.predictions[-1]  # Get latest
            stats['prediction'] = {
                'home_win_probability': latest_prediction.home_win_probability,
                'draw_probability': latest_prediction.draw_probability,
                'away_win_probability': latest_prediction.away_win_probability,
                'over_2_5_probability': latest_prediction.over_2_5_probability,
                'confidence_score': latest_prediction.confidence_score,
                'created_at': latest_prediction.created_at.isoformat()
            }
        
        return stats