"""
Example: How to update API routes with pagination and caching
This shows best practices for performance improvements
"""

from flask import Blueprint, jsonify, request
from models import db, Team, Match, Prediction
from pagination import paginated_response, PaginationParams
from cache_manager import CacheManager
from enhanced_monitoring import track_performance
from sqlalchemy.orm import joinedload
from datetime import datetime

# Initialize cache manager
cache = CacheManager()

# Example: Updated teams endpoint with pagination
@api_bp.route('/teams', methods=['GET'])
@track_performance
def get_teams():
    """Get teams with pagination and caching"""
    # Check cache first
    cache_key = f"teams:{request.query_string.decode()}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return jsonify(cached_result)
    
    # Build query
    query = Team.query
    
    # Add search filter if provided
    search = request.args.get('search')
    if search:
        query = query.filter(
            db.or_(
                Team.name.ilike(f'%{search}%'),
                Team.code.ilike(f'%{search}%')
            )
        )
    
    # Apply ordering
    query = query.order_by(Team.name)
    
    # Get paginated response
    response = paginated_response(
        query,
        serializer=lambda t: {
            'id': t.id,
            'name': t.name,
            'code': t.code,
            'logo_url': t.logo_url,
            'stadium': t.stadium,
            'founded': t.founded
        },
        endpoint='api.get_teams'
    )
    
    # Cache the result
    cache.set(cache_key, response, timeout=300)  # 5 minutes
    
    return jsonify(response)


# Example: Updated matches endpoint with efficient loading
@api_bp.route('/matches', methods=['GET'])
@track_performance
def get_matches():
    """Get matches with pagination and optimized loading"""
    # Build query with eager loading to prevent N+1 queries
    query = Match.query.options(
        joinedload(Match.home_team),
        joinedload(Match.away_team),
        joinedload(Match.competition)
    )
    
    # Filter by date if provided
    date = request.args.get('date')
    if date:
        try:
            match_date = datetime.strptime(date, '%Y-%m-%d')
            query = query.filter(
                db.func.date(Match.match_date) == match_date.date()
            )
        except ValueError:
            pass
    
    # Filter by team
    team_id = request.args.get('team_id')
    if team_id:
        query = query.filter(
            db.or_(
                Match.home_team_id == team_id,
                Match.away_team_id == team_id
            )
        )
    
    # Order by date
    query = query.order_by(Match.match_date.desc())
    
    # Get paginated response
    response = paginated_response(
        query,
        serializer=lambda m: {
            'id': m.id,
            'home_team': {
                'id': m.home_team.id,
                'name': m.home_team.name,
                'logo_url': m.home_team.logo_url
            },
            'away_team': {
                'id': m.away_team.id,
                'name': m.away_team.name,
                'logo_url': m.away_team.logo_url
            },
            'match_date': m.match_date.isoformat(),
            'status': m.status,
            'home_score': m.home_score,
            'away_score': m.away_score,
            'competition': {
                'id': m.competition.id,
                'name': m.competition.name
            } if m.competition else None
        },
        endpoint='api.get_matches'
    )
    
    return jsonify(response)


# Example: Predictions endpoint with smart caching
@api_bp.route('/predictions', methods=['GET'])
@track_performance
def get_predictions():
    """Get predictions with caching based on parameters"""
    params = PaginationParams.from_request()
    
    # Build cache key from parameters
    cache_parts = [
        f"predictions",
        f"page:{params.page}",
        f"per_page:{params.per_page}"
    ]
    
    # Add filters to cache key
    if request.args.get('date'):
        cache_parts.append(f"date:{request.args.get('date')}")
    if request.args.get('team_id'):
        cache_parts.append(f"team:{request.args.get('team_id')}")
    if request.args.get('confidence_min'):
        cache_parts.append(f"conf:{request.args.get('confidence_min')}")
    
    cache_key = ":".join(cache_parts)
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached)
    
    # Build query with joins
    query = Prediction.query.options(
        joinedload(Prediction.match).joinedload(Match.home_team),
        joinedload(Prediction.match).joinedload(Match.away_team)
    )
    
    # Apply filters
    if request.args.get('confidence_min'):
        try:
            min_conf = float(request.args.get('confidence_min'))
            query = query.filter(Prediction.confidence_score >= min_conf / 100)
        except ValueError:
            pass
    
    # Order by creation date
    query = query.order_by(Prediction.created_at.desc())
    
    # Get paginated response
    response = paginated_response(
        query,
        serializer=lambda p: {
            'id': p.id,
            'match': {
                'id': p.match.id,
                'home_team': p.match.home_team.name,
                'away_team': p.match.away_team.name,
                'match_date': p.match.match_date.isoformat()
            },
            'prediction': {
                'outcome': p.predicted_outcome,
                'home_win_probability': p.home_win_probability,
                'draw_probability': p.draw_probability,
                'away_win_probability': p.away_win_probability,
                'confidence': p.confidence_score * 100,
                'predicted_score': {
                    'home': p.predicted_home_score,
                    'away': p.predicted_away_score
                }
            },
            'created_at': p.created_at.isoformat()
        },
        endpoint='api.get_predictions'
    )
    
    # Cache for 5 minutes
    cache.set(cache_key, response, timeout=300)
    
    return jsonify(response)


# Example: Batch endpoint for multiple predictions
@api_bp.route('/predictions/batch', methods=['POST'])
@track_performance
def create_batch_predictions():
    """Create predictions for multiple matches efficiently"""
    data = request.get_json()
    match_ids = data.get('match_ids', [])
    
    if not match_ids:
        return jsonify({'error': 'No match IDs provided'}), 400
    
    # Limit batch size
    if len(match_ids) > 50:
        return jsonify({'error': 'Maximum 50 matches per batch'}), 400
    
    # Get all matches in one query
    matches = Match.query.filter(Match.id.in_(match_ids)).all()
    
    if len(matches) != len(match_ids):
        return jsonify({'error': 'Some matches not found'}), 404
    
    # Process predictions in batch
    predictions = []
    errors = []
    
    for match in matches:
        try:
            # Check if prediction already exists
            existing = Prediction.query.filter_by(match_id=match.id).first()
            if existing:
                predictions.append(existing)
                continue
            
            # Generate prediction (this would use the unified engine)
            # ... prediction logic ...
            
            predictions.append(prediction)
        except Exception as e:
            errors.append({
                'match_id': match.id,
                'error': str(e)
            })
    
    # Commit all at once
    db.session.commit()
    
    return jsonify({
        'predictions': [serialize_prediction(p) for p in predictions],
        'errors': errors,
        'summary': {
            'requested': len(match_ids),
            'created': len(predictions),
            'errors': len(errors)
        }
    })


# Performance tips implemented:
# 1. Use joinedload() to prevent N+1 queries
# 2. Cache frequently accessed data
# 3. Implement proper pagination
# 4. Use batch operations where possible
# 5. Add database indexes on filtered columns
# 6. Use query optimization techniques
# 7. Monitor performance with decorators