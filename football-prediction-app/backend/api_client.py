"""
Optimized API client with connection pooling and advanced features
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional, List
import time
import logging
from functools import wraps
import hashlib
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: int, per: int):
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current
            self.allowance += time_passed * (self.rate / self.per)
            
            if self.allowance > self.rate:
                self.allowance = self.rate
            
            if self.allowance < 1.0:
                sleep_time = (1 - self.allowance) * (self.per / self.rate)
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self.allowance = 0
            else:
                self.allowance -= 1
            
            return func(*args, **kwargs)
        return wrapper


class OptimizedAPIClient:
    """Base API client with connection pooling and optimizations"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, 
                 rate_limit: Optional[tuple] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        
        # Create session with connection pooling
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        # Mount adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=retry_strategy
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'FootballPredictionAPI/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Set up rate limiting if specified
        if rate_limit:
            rate, per = rate_limit
            self.rate_limiter = RateLimiter(rate, per)
        else:
            self.rate_limiter = None
        
        # Response cache
        self._cache: Dict[str, tuple] = {}
        self.cache_ttl = 300  # 5 minutes default
    
    def _get_cache_key(self, method: str, url: str, params: Optional[Dict] = None) -> str:
        """Generate cache key for request"""
        cache_data = f"{method}:{url}:{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_time: datetime) -> bool:
        """Check if cached response is still valid"""
        return (datetime.now() - cached_time).total_seconds() < self.cache_ttl
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with rate limiting"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Apply rate limiting if configured
        if self.rate_limiter:
            @self.rate_limiter
            def _request():
                return self.session.request(method, url, **kwargs)
            return _request()
        else:
            return self.session.request(method, url, **kwargs)
    
    def get(self, endpoint: str, params: Optional[Dict] = None, 
            use_cache: bool = True, **kwargs) -> Dict[str, Any]:
        """GET request with caching"""
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key("GET", endpoint, params)
            if cache_key in self._cache:
                response, cached_time = self._cache[cache_key]
                if self._is_cache_valid(cached_time):
                    logger.debug(f"Cache hit for {endpoint}")
                    return response
        
        # Add API key if available
        if self.api_key:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers']['Authorization'] = f"Bearer {self.api_key}"
        
        try:
            response = self._make_request("GET", endpoint, params=params, **kwargs)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache successful responses
            if use_cache and response.status_code == 200:
                cache_key = self._get_cache_key("GET", endpoint, params)
                self._cache[cache_key] = (data, datetime.now())
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {endpoint}: {str(e)}")
            raise
    
    def post(self, endpoint: str, json_data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """POST request"""
        if self.api_key:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers']['Authorization'] = f"Bearer {self.api_key}"
        
        try:
            response = self._make_request("POST", endpoint, json=json_data, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"POST request failed for {endpoint}: {str(e)}")
            raise
    
    def put(self, endpoint: str, json_data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """PUT request"""
        if self.api_key:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers']['Authorization'] = f"Bearer {self.api_key}"
        
        try:
            response = self._make_request("PUT", endpoint, json=json_data, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"PUT request failed for {endpoint}: {str(e)}")
            raise
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request"""
        if self.api_key:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers']['Authorization'] = f"Bearer {self.api_key}"
        
        try:
            response = self._make_request("DELETE", endpoint, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"DELETE request failed for {endpoint}: {str(e)}")
            raise
    
    def batch_get(self, endpoints: List[str], use_cache: bool = True) -> List[Dict[str, Any]]:
        """Batch GET requests with concurrent execution"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_endpoint = {
                executor.submit(self.get, endpoint, use_cache=use_cache): endpoint 
                for endpoint in endpoints
            }
            
            for future in as_completed(future_to_endpoint):
                endpoint = future_to_endpoint[future]
                try:
                    data = future.result()
                    results.append({'endpoint': endpoint, 'data': data, 'error': None})
                except Exception as e:
                    logger.error(f"Batch request failed for {endpoint}: {str(e)}")
                    results.append({'endpoint': endpoint, 'data': None, 'error': str(e)})
        
        return results
    
    def clear_cache(self):
        """Clear response cache"""
        self._cache.clear()
        logger.info("API client cache cleared")
    
    def close(self):
        """Close session and clean up resources"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SportMonksOptimizedClient(OptimizedAPIClient):
    """Optimized SportMonks API client"""
    
    def __init__(self, api_key: str):
        super().__init__(
            base_url="https://api.sportmonks.com/v3/football",
            api_key=api_key,
            rate_limit=(60, 60)  # 60 requests per minute
        )
        
        # SportMonks specific headers
        self.session.headers.update({
            'Accept': 'application/json'
        })
    
    def get(self, endpoint: str, params: Optional[Dict] = None, 
            use_cache: bool = True, **kwargs) -> Dict[str, Any]:
        """Override to add API token to params for SportMonks"""
        if params is None:
            params = {}
        params['api_token'] = self.api_key
        
        # Remove auth header as SportMonks uses query param
        if 'headers' in kwargs and 'Authorization' in kwargs['headers']:
            del kwargs['headers']['Authorization']
        
        return super().get(endpoint, params, use_cache, **kwargs)