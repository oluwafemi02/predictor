"""
Live SportMonks data - fetch directly without database
"""
import os
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class LiveSportMonks:
    """Fetch SportMonks data live without database"""
    
    def __init__(self):
        self.api_key = os.environ.get('SPORTMONKS_API_KEY')
        self.base_url = "https://api.sportmonks.com/v3/football"
        self.headers = {"Authorization": self.api_key} if self.api_key else {}
    
    def get_fixtures(self, status=None, page=1, per_page=20):
        """Get fixtures directly from SportMonks API"""
        
        if not self.api_key:
            return {
                'data': [],
                'page': page,
                'total_pages': 0,
                'total_items': 0,
                'page_size': per_page,
                'error': 'No API key configured'
            }
        
        try:
            # Get fixtures for date range
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/fixtures/between/{start_date}/{end_date}"
            params = {
                "include": "participants;league;venue;state;scores",
                "page": page,
                "per_page": per_page
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                logger.error(f"SportMonks API error: {response.status_code}")
                return {
                    'data': [],
                    'page': page,
                    'total_pages': 0,
                    'total_items': 0,
                    'page_size': per_page,
                    'error': f'API error: {response.status_code}'
                }
            
            data = response.json()
            fixtures = data.get('data', [])
            
            # Transform to match expected format
            transformed_fixtures = []
            
            for fixture in fixtures:
                # Extract teams from participants
                participants = fixture.get('participants', [])
                home_team = None
                away_team = None
                
                for p in participants:
                    if p.get('meta', {}).get('location') == 'home':
                        home_team = p
                    elif p.get('meta', {}).get('location') == 'away':
                        away_team = p
                
                if not home_team or not away_team:
                    continue
                
                # Get scores
                home_score = None
                away_score = None
                scores = fixture.get('scores', [])
                for score in scores:
                    if score.get('description') == 'CURRENT':
                        s = score.get('score', {})
                        home_score = s.get('home')
                        away_score = s.get('away')
                        break
                
                # Map state to status
                state = fixture.get('state', {})
                state_name = state.get('name', '').lower()
                
                if state_name in ['ft', 'aet', 'ft_pens']:
                    status = 'finished'
                elif state_name in ['live', 'ht', 'et', 'pen_live']:
                    status = 'live'
                elif state_name in ['ns', 'tba', 'postponed', 'cancelled']:
                    status = 'scheduled'
                else:
                    status = state_name
                
                # Filter by status if requested
                if status and status != 'all':
                    if status == 'upcoming' and state_name != 'ns':
                        continue
                    elif status == 'finished' and state_name not in ['ft', 'aet', 'ft_pens']:
                        continue
                    elif status == 'live' and state_name not in ['live', 'ht', 'et']:
                        continue
                
                transformed_fixtures.append({
                    'id': fixture.get('id'),
                    'home_team': {
                        'id': home_team.get('id'),
                        'name': home_team.get('name'),
                        'logo_url': home_team.get('image_path', '')
                    },
                    'away_team': {
                        'id': away_team.get('id'),
                        'name': away_team.get('name'),
                        'logo_url': away_team.get('image_path', '')
                    },
                    'match_date': fixture.get('starting_at'),
                    'home_score': home_score,
                    'away_score': away_score,
                    'status': status,
                    'venue': fixture.get('venue', {}).get('name', 'Unknown'),
                    'competition': fixture.get('league', {}).get('name', 'Unknown League'),
                    'has_prediction': False  # Would need predictions endpoint
                })
            
            # Calculate pagination
            meta = data.get('meta', {})
            total_items = meta.get('total', len(transformed_fixtures))
            total_pages = meta.get('last_page', 1)
            
            return {
                'data': transformed_fixtures,
                'page': page,
                'total_pages': total_pages,
                'total_items': total_items,
                'page_size': per_page,
                'data_source': 'sportmonks_live'
            }
            
        except Exception as e:
            logger.error(f"Error fetching live SportMonks data: {str(e)}")
            return {
                'data': [],
                'page': page,
                'total_pages': 0,
                'total_items': 0,
                'page_size': per_page,
                'error': str(e)
            }
    
    def get_teams(self, page=1, per_page=20):
        """Get teams directly from SportMonks API"""
        
        if not self.api_key:
            return {
                'data': [],
                'page': page,
                'total_pages': 0,
                'total_items': 0,
                'page_size': per_page
            }
        
        try:
            # For now, extract teams from recent fixtures
            fixtures_data = self.get_fixtures(page=1, per_page=100)
            fixtures = fixtures_data.get('data', [])
            
            # Extract unique teams
            teams_dict = {}
            
            for fixture in fixtures:
                home = fixture.get('home_team', {})
                away = fixture.get('away_team', {})
                
                for team in [home, away]:
                    if team.get('id') and team['id'] not in teams_dict:
                        teams_dict[team['id']] = {
                            'id': team['id'],
                            'name': team.get('name', 'Unknown'),
                            'logo_url': team.get('logo_url', ''),
                            'matches_played': 0,
                            'wins': 0,
                            'draws': 0,
                            'losses': 0,
                            'goals_for': 0,
                            'goals_against': 0,
                            'points': 0
                        }
            
            teams = list(teams_dict.values())
            
            # Paginate
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_teams = teams[start_idx:end_idx]
            
            return {
                'data': paginated_teams,
                'page': page,
                'total_pages': max(1, len(teams) // per_page + (1 if len(teams) % per_page else 0)),
                'total_items': len(teams),
                'page_size': per_page,
                'data_source': 'sportmonks_live'
            }
            
        except Exception as e:
            logger.error(f"Error fetching live teams data: {str(e)}")
            return {
                'data': [],
                'page': page,
                'total_pages': 0,
                'total_items': 0,
                'page_size': per_page
            }