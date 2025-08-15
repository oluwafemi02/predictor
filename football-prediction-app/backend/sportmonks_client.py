import requests
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
from functools import wraps
import redis
from config import Config
import hashlib
import os
from security import TokenManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SportMonksAPIClient:
    """
    SportMonks Football API v3 Client with advanced features:
    - Multiple API token support with automatic fallback
    - Redis caching for improved performance
    - Rate limiting and retry logic
    - Comprehensive error handling
    - Secure token storage
    """
    
    def __init__(self):
        # Initialize token manager for secure storage
        self.token_manager = TokenManager()
        
        # Primary token from environment variables - stored securely
        primary_token_raw = os.environ.get('SPORTMONKS_PRIMARY_TOKEN')
        if not primary_token_raw:
            logger.warning("SPORTMONKS_PRIMARY_TOKEN not set, using fallback tokens only")
            primary_token_raw = Config.SPORTMONKS_API_KEY
        
        self.primary_token = primary_token_raw if primary_token_raw else None
        
        # Fallback tokens from environment variables
        self.fallback_tokens = []
        if Config.SPORTMONKS_API_KEY and Config.SPORTMONKS_API_KEY != self.primary_token:
            self.fallback_tokens.append(Config.SPORTMONKS_API_KEY)
        
        # Additional fallback tokens can be added here
        env_tokens = os.environ.get('SPORTMONKS_FALLBACK_TOKENS', '').split(',')
        self.fallback_tokens.extend([t.strip() for t in env_tokens if t.strip()])
        
        # Log token status (masked for security)
        if self.primary_token:
            logger.info(f"Primary token configured: {self.token_manager.mask_token(self.primary_token)}")
        else:
            logger.info("No primary token configured, using fallback tokens only")
        logger.info(f"Fallback tokens available: {len(self.fallback_tokens)}")
        
        # Current active token
        self.current_token = self.primary_token
        self.token_index = -1  # -1 for primary, 0+ for fallbacks
        
        # API configuration
        self.base_url = "https://api.sportmonks.com/v3/football"
        self.timeout = 15  # Reduced timeout to prevent 502 errors
        
        # Redis client for caching
        try:
            self.redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            self.cache_enabled = True
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis cache not available: {str(e)}")
            self.redis_client = None
            self.cache_enabled = False
        
        # Rate limiting
        self.rate_limit_remaining = 1000
        self.rate_limit_reset = None
        
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate a unique cache key for the request"""
        param_str = json.dumps(params, sort_keys=True)
        key_data = f"{endpoint}:{param_str}"
        return f"sportmonks:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Retrieve data from cache if available"""
        if not self.cache_enabled:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for key: {cache_key}")
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Cache retrieval error: {str(e)}")
        
        return None
    
    def _set_cache(self, cache_key: str, data: Dict, ttl: int = 300):
        """Store data in cache with TTL"""
        if not self.cache_enabled:
            return
        
        try:
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data)
            )
            logger.debug(f"Cached data for key: {cache_key} with TTL: {ttl}s")
        except Exception as e:
            logger.error(f"Cache storage error: {str(e)}")
    
    def _switch_to_next_token(self) -> bool:
        """Switch to the next available token"""
        if self.token_index == -1:
            # Currently using primary, switch to first fallback
            if self.fallback_tokens:
                self.token_index = 0
                self.current_token = self.fallback_tokens[0]
                logger.warning("Switched to fallback token 0")
                return True
        elif self.token_index < len(self.fallback_tokens) - 1:
            # Switch to next fallback
            self.token_index += 1
            self.current_token = self.fallback_tokens[self.token_index]
            logger.warning(f"Switched to fallback token {self.token_index}")
            return True
        
        logger.error("All API tokens exhausted")
        return False
    
    def _make_request(self, endpoint: str, params: Dict = None, use_cache: bool = True, cache_ttl: int = 300) -> Optional[Dict]:
        """
        Make an API request with automatic retry and token fallback
        """
        if params is None:
            params = {}
        
        # Add API token to params
        params['api_token'] = self.current_token
        
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(endpoint, params)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        url = f"{self.base_url}/{endpoint}"
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Making request to: {endpoint}")
                response = requests.get(url, params=params, timeout=self.timeout)
                
                # Update rate limit info
                if 'X-RateLimit-Remaining' in response.headers:
                    self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
                if 'X-RateLimit-Reset' in response.headers:
                    self.rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
                
                # Handle rate limiting
                if response.status_code == 429:
                    logger.warning("Rate limit reached")
                    if self._switch_to_next_token():
                        params['api_token'] = self.current_token
                        retry_count = 0  # Reset retry count for new token
                        continue
                    else:
                        # Wait for rate limit reset if no more tokens
                        if self.rate_limit_reset:
                            wait_time = self.rate_limit_reset - int(time.time())
                            if wait_time > 0:
                                logger.info(f"Waiting {wait_time}s for rate limit reset")
                                time.sleep(wait_time)
                                retry_count += 1
                                continue
                
                # Handle authentication errors
                if response.status_code in [401, 403]:
                    logger.error(f"Authentication error with current token: {response.status_code}")
                    if self._switch_to_next_token():
                        params['api_token'] = self.current_token
                        retry_count = 0
                        continue
                    else:
                        return None
                
                response.raise_for_status()
                data = response.json()
                
                # Cache successful response
                if use_cache and 'data' in data:
                    self._set_cache(cache_key, data, cache_ttl)
                
                return data
                
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout for endpoint: {endpoint}")
                retry_count += 1
                time.sleep(2 ** retry_count)  # Exponential backoff
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {str(e)}")
                retry_count += 1
                time.sleep(2 ** retry_count)
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                return None
        
        logger.error(f"Max retries exceeded for endpoint: {endpoint}")
        return None
    
    # Core API Methods
    
    def get_fixtures(self, date: Optional[str] = None, league_id: Optional[int] = None, 
                     include: List[str] = None, filters: Dict = None) -> Optional[Dict]:
        """
        Get fixtures with optional filters
        
        Args:
            date: Date in YYYY-MM-DD format
            league_id: Filter by league ID
            include: List of relations to include (e.g., ['localTeam', 'visitorTeam', 'odds'])
            filters: Additional filters
        """
        params = {}
        if date:
            params['filter[date]'] = date
        if league_id:
            params['filter[league_id]'] = league_id
        if include:
            params['include'] = ','.join(include)
        if filters:
            for key, value in filters.items():
                params[f'filter[{key}]'] = value
        
        return self._make_request('fixtures', params)
    
    def get_fixture_by_id(self, fixture_id: int, include: List[str] = None) -> Optional[Dict]:
        """Get detailed information about a specific fixture"""
        params = {}
        if include:
            params['include'] = ','.join(include)
        
        return self._make_request(f'fixtures/{fixture_id}', params)
    
    def get_predictions_by_fixture(self, fixture_id: int) -> Optional[Dict]:
        """Get predictions for a specific fixture"""
        return self._make_request(f'predictions/fixtures/{fixture_id}')
    
    def get_value_bets_by_fixture(self, fixture_id: int) -> Optional[Dict]:
        """Get value bet analysis for a specific fixture"""
        return self._make_request(f'predictions/value-bets/fixtures/{fixture_id}')
    
    def get_probabilities_by_fixture(self, fixture_id: int) -> Optional[Dict]:
        """Get match outcome probabilities for a specific fixture"""
        return self._make_request(f'predictions/probabilities/fixtures/{fixture_id}')
    
    def get_live_scores(self, include: List[str] = None) -> Optional[Dict]:
        """Get all currently live fixtures"""
        params = {}
        if include:
            params['include'] = ','.join(include)
        
        # Use shorter cache TTL for live data
        return self._make_request('livescores', params, cache_ttl=30)
    
    def get_team_by_id(self, team_id: int, include: List[str] = None) -> Optional[Dict]:
        """Get detailed team information"""
        params = {}
        if include:
            params['include'] = ','.join(include)
        
        return self._make_request(f'teams/{team_id}', params, cache_ttl=3600)
    
    def get_player_by_id(self, player_id: int, include: List[str] = None) -> Optional[Dict]:
        """Get detailed player information"""
        params = {}
        if include:
            params['include'] = ','.join(include)
        
        return self._make_request(f'players/{player_id}', params, cache_ttl=3600)
    
    def get_standings(self, season_id: int, include: List[str] = None) -> Optional[Dict]:
        """Get league standings for a season"""
        params = {}
        if include:
            params['include'] = ','.join(include)
        
        return self._make_request(f'standings/seasons/{season_id}', params, cache_ttl=1800)
    
    def get_topscorers(self, season_id: int, include: List[str] = None) -> Optional[Dict]:
        """Get top scorers for a season"""
        params = {}
        if include:
            params['include'] = ','.join(include)
        
        return self._make_request(f'topscorers/seasons/{season_id}', params, cache_ttl=1800)
    
    def get_h2h(self, team_ids: List[int]) -> Optional[Dict]:
        """Get head-to-head data between teams"""
        params = {
            'team_ids': ','.join(map(str, team_ids))
        }
        
        return self._make_request('head2head', params, cache_ttl=3600)
    
    def get_odds_by_fixture(self, fixture_id: int, bookmaker_id: Optional[int] = None) -> Optional[Dict]:
        """Get odds for a specific fixture"""
        params = {}
        if bookmaker_id:
            params['filter[bookmaker_id]'] = bookmaker_id
        
        return self._make_request(f'odds/fixtures/{fixture_id}', params, cache_ttl=600)
    
    def get_in_play_odds(self, fixture_id: int) -> Optional[Dict]:
        """Get in-play odds for a live fixture"""
        return self._make_request(f'odds/inplay/fixtures/{fixture_id}', cache_ttl=10)
    
    def search_teams(self, query: str) -> Optional[Dict]:
        """Search for teams by name"""
        params = {'name': query}
        return self._make_request('teams/search', params=params)
    
    def get_teams_by_league(self, league_id: int, include: List[str] = None) -> Optional[Dict]:
        """Get all teams in a specific league"""
        endpoint = f'teams/league/{league_id}'
        params = {}
        if include:
            params['include'] = ','.join(include)
        return self._make_request(endpoint, params=params)
    
    def get_seasons(self, league_id: Optional[int] = None) -> Optional[Dict]:
        """Get available seasons"""
        params = {}
        if league_id:
            params['filter[league_id]'] = league_id
        
        return self._make_request('seasons', params, cache_ttl=86400)
    
    def get_leagues(self, include: List[str] = None) -> Optional[Dict]:
        """Get all available leagues"""
        params = {}
        if include:
            params['include'] = ','.join(include)
        
        return self._make_request('leagues', params, cache_ttl=86400)
    
    # Batch operations for efficiency
    
    def get_fixtures_by_date_range(self, start_date: str, end_date: str, 
                                   league_ids: List[int] = None, 
                                   team_id: int = None,
                                   include: List[str] = None) -> List[Dict]:
        """Get all fixtures within a date range"""
        # Use betweenDates filter for more efficient API call
        params = {
            'filter[betweenDates]': f'{start_date},{end_date}'
        }
        
        if team_id:
            params['filter[team_id]'] = team_id
        
        if league_ids and len(league_ids) == 1:
            params['filter[league_id]'] = league_ids[0]
        elif league_ids and len(league_ids) > 1:
            # For multiple leagues, we need to make separate calls
            all_fixtures = []
            for league_id in league_ids:
                params['filter[league_id]'] = league_id
                result = self._make_request('fixtures', params, cache_ttl=600)
                if result and 'data' in result:
                    all_fixtures.extend(result['data'])
            return all_fixtures
        
        if include:
            params['include'] = ','.join(include)
        
        # Make a single API call for the date range
        result = self._make_request('fixtures', params, cache_ttl=600)
        
        if result and 'data' in result:
            return result['data']
        
        return []
    
    def get_predictions_for_date(self, date: str) -> List[Dict]:
        """Get all predictions for fixtures on a specific date"""
        fixtures = self.get_fixtures(date=date)
        predictions = []
        
        if fixtures and 'data' in fixtures:
            for fixture in fixtures['data']:
                prediction = self.get_predictions_by_fixture(fixture['id'])
                if prediction and 'data' in prediction:
                    predictions.append({
                        'fixture': fixture,
                        'prediction': prediction['data']
                    })
        
        return predictions
    
    # Health check and status methods
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health and token status"""
        result = {
            'api_status': 'unknown',
            'current_token_index': self.token_index,
            'tokens_available': 1 + len(self.fallback_tokens),
            'rate_limit_remaining': self.rate_limit_remaining,
            'cache_enabled': self.cache_enabled,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Try a simple API call
        test_response = self._make_request('leagues', {'per_page': 1}, use_cache=False)
        if test_response:
            result['api_status'] = 'healthy'
            result['response_time_ms'] = test_response.get('time', {}).get('elapsed', 0)
        else:
            result['api_status'] = 'unhealthy'
        
        return result
    
    # Generic method for accessing any endpoint
    def get(self, endpoint: str, params: Dict = None, include: List[str] = None, cache_ttl: int = 300) -> Optional[Dict]:
        """
        Generic method to access any SportMonks API endpoint
        
        Args:
            endpoint: The API endpoint (e.g., 'schedules/teams/123')
            params: Additional query parameters
            include: List of relations to include
            cache_ttl: Cache time-to-live in seconds
        """
        if params is None:
            params = {}
        
        if include:
            if isinstance(include, list):
                params['include'] = ','.join(include)
            else:
                params['include'] = include
        
        return self._make_request(endpoint, params, cache_ttl=cache_ttl)