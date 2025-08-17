import requests
import os
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

class SportMonksV3Client:
    """
    Simplified SportMonks Football API v3 Client with proper field selection
    Based on the official documentation
    """
    
    def __init__(self):
        self.api_key = os.environ.get('SPORTMONKS_API_KEY') or os.environ.get('SPORTMONKS_PRIMARY_TOKEN')
        if not self.api_key:
            raise ValueError("SportMonks API key not found in environment variables")
        
        self.base_url = "https://api.sportmonks.com/v3/football"
        self.timeout = 30
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a request to the SportMonks API with proper error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        # Add API token to params
        if params is None:
            params = {}
        params['api_token'] = self.api_key
        
        try:
            logger.info(f"Making request to: {endpoint}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if 'error' in data:
                logger.error(f"API error: {data['error']}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {endpoint}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {str(e)}")
            return None
    
    # Fixture endpoints based on documentation
    
    def get_all_fixtures(self, include: str = None, select: str = None) -> Optional[Dict]:
        """Get all fixtures accessible within your subscription"""
        params = {}
        if include:
            params['include'] = include
        if select:
            params['select'] = select
        
        return self._make_request('fixtures', params)
    
    def get_fixture_by_id(self, fixture_id: int, include: str = None, select: str = None) -> Optional[Dict]:
        """Get a single fixture by ID"""
        params = {}
        if include:
            params['include'] = include
        if select:
            params['select'] = select
        
        return self._make_request(f'fixtures/{fixture_id}', params)
    
    def get_fixtures_by_multiple_ids(self, fixture_ids: List[int], include: str = None, select: str = None) -> Optional[Dict]:
        """Get multiple fixtures by IDs"""
        params = {}
        if include:
            params['include'] = include
        if select:
            params['select'] = select
        
        ids_str = ','.join(str(id) for id in fixture_ids)
        return self._make_request(f'fixtures/multi/{ids_str}', params)
    
    def get_fixtures_by_date(self, date: str, include: str = None, select: str = None) -> Optional[Dict]:
        """Get fixtures for a specific date (YYYY-MM-DD format)"""
        params = {}
        if include:
            params['include'] = include
        if select:
            params['select'] = select
        
        return self._make_request(f'fixtures/date/{date}', params)
    
    def get_fixtures_by_date_range(self, start_date: str, end_date: str, include: str = None, select: str = None) -> Optional[Dict]:
        """Get fixtures between two dates (YYYY-MM-DD format)"""
        params = {}
        if include:
            params['include'] = include
        if select:
            params['select'] = select
        
        return self._make_request(f'fixtures/between/{start_date}/{end_date}', params)
    
    def get_fixtures_by_date_range_for_team(self, start_date: str, end_date: str, team_id: int, include: str = None, select: str = None) -> Optional[Dict]:
        """Get fixtures for a specific team between two dates"""
        params = {}
        if include:
            params['include'] = include
        if select:
            params['select'] = select
        
        return self._make_request(f'fixtures/between/{start_date}/{end_date}/{team_id}', params)
    
    def get_fixtures_by_head_to_head(self, team1_id: int, team2_id: int, include: str = None, select: str = None) -> Optional[Dict]:
        """Get head-to-head fixtures between two teams"""
        params = {}
        if include:
            params['include'] = include
        if select:
            params['select'] = select
        
        return self._make_request(f'fixtures/head-to-head/{team1_id}/{team2_id}', params)
    
    def search_fixtures_by_name(self, search_query: str, include: str = None, select: str = None) -> Optional[Dict]:
        """Search fixtures by team name"""
        params = {}
        if include:
            params['include'] = include
        if select:
            params['select'] = select
        
        return self._make_request(f'fixtures/search/{search_query}', params)
    
    def get_upcoming_fixtures_by_market_id(self, market_id: int, include: str = None, select: str = None) -> Optional[Dict]:
        """Get upcoming fixtures that have odds for a specific market"""
        params = {}
        if include:
            params['include'] = include
        if select:
            params['select'] = select
        
        return self._make_request(f'fixtures/upcoming/markets/{market_id}', params)
    
    def get_latest_updated_fixtures(self, include: str = None, select: str = None) -> Optional[Dict]:
        """Get fixtures that have been updated within the last 10 seconds"""
        params = {}
        if include:
            params['include'] = include
        if select:
            params['select'] = select
        
        return self._make_request('fixtures/latest', params)
    
    # Helper methods for common use cases
    
    def get_upcoming_fixtures(self, days: int = 7, include: str = None) -> Optional[Dict]:
        """Get upcoming fixtures for the next N days"""
        today = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Default includes for prediction functionality
        if not include:
            include = 'scores;participants;statistics.type;events;lineups'
        
        return self.get_fixtures_by_date_range(today, end_date, include=include)
    
    def get_past_fixtures(self, days: int = 7, include: str = None) -> Optional[Dict]:
        """Get past fixtures for the last N days"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Default includes for analysis
        if not include:
            include = 'scores;participants;statistics.type;events;lineups'
        
        return self.get_fixtures_by_date_range(start_date, end_date, include=include)
    
    def get_todays_fixtures(self, include: str = None) -> Optional[Dict]:
        """Get today's fixtures"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Default includes
        if not include:
            include = 'scores;participants;statistics.type;events;lineups'
        
        return self.get_fixtures_by_date(today, include=include)
    
    # Livescores endpoint for in-play fixtures
    def get_live_fixtures(self, include: str = None) -> Optional[Dict]:
        """Get live fixtures (in-play)"""
        params = {}
        if include:
            params['include'] = include
        else:
            params['include'] = 'scores;participants;events'
        
        return self._make_request('livescores', params)
    
    # Team endpoints
    def get_team_by_id(self, team_id: int, include: str = None, select: str = None) -> Optional[Dict]:
        """Get team information by ID"""
        params = {}
        if include:
            params['include'] = include
        if select:
            params['select'] = select
        
        return self._make_request(f'teams/{team_id}', params)
    
    # League endpoints
    def get_leagues(self, include: str = None) -> Optional[Dict]:
        """Get all leagues"""
        params = {}
        if include:
            params['include'] = include
        
        return self._make_request('leagues', params)
    
    # Standings endpoint
    def get_standings_by_season(self, season_id: int, include: str = None) -> Optional[Dict]:
        """Get standings for a season"""
        params = {}
        if include:
            params['include'] = include
        
        return self._make_request(f'standings/seasons/{season_id}', params)
    
    # Statistics endpoints
    def get_team_statistics(self, team_id: int, season_id: int = None) -> Optional[Dict]:
        """Get team statistics"""
        endpoint = f'teams/{team_id}/statistics'
        params = {}
        if season_id:
            params['filters'] = f'season_id:{season_id}'
        
        return self._make_request(endpoint, params)