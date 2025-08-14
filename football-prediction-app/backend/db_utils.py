"""
Database utilities for optimized queries and connection management
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import joinedload, selectinload, subqueryload
from sqlalchemy import and_, or_, func
from models import db, Match, Team, Prediction, TeamStatistics
import logging

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def get_matches_with_relations(
        status: Optional[str] = None,
        competition: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Match], Dict[str, Any]]:
        """
        Get matches with eager loaded relationships to prevent N+1 queries
        """
        query = Match.query.options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            selectinload(Match.predictions),
            selectinload(Match.odds)
        )
        
        # Apply filters
        if status:
            query = query.filter(Match.status == status)
        if competition:
            query = query.filter(Match.competition == competition)
        
        # Order by date
        query = query.order_by(Match.match_date.desc())
        
        # Paginate
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return paginated.items, {
            'total': paginated.total,
            'pages': paginated.pages,
            'page': page,
            'per_page': per_page
        }
    
    @staticmethod
    def get_team_with_stats(team_id: int, season: Optional[str] = None) -> Optional[Team]:
        """
        Get team with all related statistics eager loaded
        """
        query = Team.query.options(
            selectinload(Team.statistics),
            selectinload(Team.players).selectinload('injuries'),
            subqueryload(Team.home_matches).options(
                joinedload(Match.away_team)
            ).limit(10),
            subqueryload(Team.away_matches).options(
                joinedload(Match.home_team)
            ).limit(10)
        )
        
        team = query.get(team_id)
        
        if team and season:
            # Filter statistics to specific season
            team.statistics = [s for s in team.statistics if s.season == season]
        
        return team
    
    @staticmethod
    def get_upcoming_matches_for_prediction(limit: int = 50) -> List[Match]:
        """
        Get upcoming matches that need predictions
        """
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        week_ahead = now + timedelta(days=7)
        
        matches = Match.query.options(
            joinedload(Match.home_team).joinedload(Team.statistics),
            joinedload(Match.away_team).joinedload(Team.statistics),
            selectinload(Match.predictions)
        ).filter(
            and_(
                Match.match_date >= now,
                Match.match_date <= week_ahead,
                Match.status == 'scheduled'
            )
        ).order_by(Match.match_date).limit(limit).all()
        
        # Filter out matches that already have recent predictions
        matches_needing_prediction = []
        for match in matches:
            if not match.predictions or (
                match.predictions and 
                (now - match.predictions[-1].created_at).days > 1
            ):
                matches_needing_prediction.append(match)
        
        return matches_needing_prediction
    
    @staticmethod
    def bulk_create_predictions(predictions_data: List[Dict[str, Any]]) -> int:
        """
        Bulk create predictions for better performance
        """
        try:
            predictions = [Prediction(**data) for data in predictions_data]
            db.session.bulk_save_objects(predictions)
            db.session.commit()
            return len(predictions)
        except Exception as e:
            logger.error(f"Bulk prediction creation failed: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def get_team_form_stats(team_id: int, num_matches: int = 5) -> Dict[str, Any]:
        """
        Get team's recent form statistics efficiently
        """
        # Get recent matches in one query
        recent_matches = Match.query.filter(
            or_(
                Match.home_team_id == team_id,
                Match.away_team_id == team_id
            ),
            Match.status == 'finished'
        ).order_by(Match.match_date.desc()).limit(num_matches).all()
        
        wins = draws = losses = goals_for = goals_against = 0
        form_string = ""
        
        for match in recent_matches:
            if match.home_team_id == team_id:
                goals_for += match.home_score or 0
                goals_against += match.away_score or 0
                
                if match.home_score > match.away_score:
                    wins += 1
                    form_string = "W" + form_string
                elif match.home_score == match.away_score:
                    draws += 1
                    form_string = "D" + form_string
                else:
                    losses += 1
                    form_string = "L" + form_string
            else:
                goals_for += match.away_score or 0
                goals_against += match.home_score or 0
                
                if match.away_score > match.home_score:
                    wins += 1
                    form_string = "W" + form_string
                elif match.away_score == match.home_score:
                    draws += 1
                    form_string = "D" + form_string
                else:
                    losses += 1
                    form_string = "L" + form_string
        
        matches_played = len(recent_matches)
        
        return {
            'matches_played': matches_played,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'goals_per_match': goals_for / matches_played if matches_played > 0 else 0,
            'goals_conceded_per_match': goals_against / matches_played if matches_played > 0 else 0,
            'form': form_string[:5],  # Last 5 matches
            'points': (wins * 3) + draws,
            'win_rate': (wins / matches_played * 100) if matches_played > 0 else 0
        }
    
    @staticmethod
    def optimize_head_to_head_query(team1_id: int, team2_id: int, limit: int = 10) -> List[Match]:
        """
        Get head-to-head matches efficiently
        """
        return Match.query.options(
            joinedload(Match.home_team),
            joinedload(Match.away_team)
        ).filter(
            or_(
                and_(Match.home_team_id == team1_id, Match.away_team_id == team2_id),
                and_(Match.home_team_id == team2_id, Match.away_team_id == team1_id)
            ),
            Match.status == 'finished'
        ).order_by(Match.match_date.desc()).limit(limit).all()


class ConnectionPoolManager:
    """Manage database connection pooling"""
    
    @staticmethod
    def get_pool_status() -> Dict[str, Any]:
        """Get current connection pool status"""
        engine = db.engine
        pool = engine.pool
        
        return {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total': pool.size() + pool.overflow()
        }
    
    @staticmethod
    def reset_pool():
        """Reset connection pool (use with caution)"""
        try:
            db.engine.dispose()
            logger.info("Database connection pool reset successfully")
        except Exception as e:
            logger.error(f"Failed to reset connection pool: {str(e)}")
            raise