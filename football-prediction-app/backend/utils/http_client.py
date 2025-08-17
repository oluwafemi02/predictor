"""
Resilient HTTP client with retry logic, timeouts, and circuit breaker
"""
import requests
from functools import wraps
import time
import logging
from typing import Optional, Dict, Any, Union
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple circuit breaker implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'half-open':
                self.state = 'closed'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise e


# Circuit breakers for different services
sportmonks_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
rapidapi_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def resilient_request(
    method: str,
    url: str,
    timeout: Optional[int] = 10,
    circuit_breaker: Optional[CircuitBreaker] = None,
    **kwargs
) -> requests.Response:
    """
    Make an HTTP request with retry logic and circuit breaker
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: URL to request
        timeout: Request timeout in seconds
        circuit_breaker: Optional circuit breaker instance
        **kwargs: Additional arguments for requests
    
    Returns:
        Response object
    
    Raises:
        requests.exceptions.RequestException: On request failure after retries
    """
    def make_request():
        kwargs.setdefault('timeout', timeout)
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    
    if circuit_breaker:
        return circuit_breaker.call(make_request)
    else:
        return make_request()


def get(url: str, **kwargs) -> requests.Response:
    """Convenience method for GET requests"""
    return resilient_request('GET', url, **kwargs)


def post(url: str, **kwargs) -> requests.Response:
    """Convenience method for POST requests"""
    return resilient_request('POST', url, **kwargs)


def sportmonks_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Make a request to SportMonks API with circuit breaker
    
    Args:
        endpoint: API endpoint (without base URL)
        params: Query parameters
    
    Returns:
        JSON response data
    """
    from config import Config
    
    base_url = Config.SPORTMONKS_API_BASE_URL
    url = f"{base_url}/{endpoint.lstrip('/')}"
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {Config.SPORTMONKS_API_KEY}'
    }
    
    response = resilient_request(
        'GET',
        url,
        params=params,
        headers=headers,
        circuit_breaker=sportmonks_circuit_breaker
    )
    
    return response.json()


def rapidapi_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Make a request to RapidAPI with circuit breaker
    
    Args:
        endpoint: API endpoint
        params: Query parameters
    
    Returns:
        JSON response data
    """
    from config import Config
    
    headers = {
        'X-RapidAPI-Key': Config.RAPIDAPI_KEY,
        'X-RapidAPI-Host': Config.RAPIDAPI_HOST
    }
    
    response = resilient_request(
        'GET',
        endpoint,
        params=params,
        headers=headers,
        circuit_breaker=rapidapi_circuit_breaker
    )
    
    return response.json()


class APIClient:
    """
    Unified API client with monitoring and metrics
    """
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.total_latency = 0
    
    def request(self, method: str, url: str, **kwargs) -> Union[requests.Response, None]:
        """Make a monitored request"""
        start_time = time.time()
        self.request_count += 1
        
        try:
            response = resilient_request(method, url, **kwargs)
            latency = time.time() - start_time
            self.total_latency += latency
            
            logger.info(f"{method} {url} - {response.status_code} - {latency:.2f}s")
            return response
            
        except Exception as e:
            self.error_count += 1
            latency = time.time() - start_time
            self.total_latency += latency
            
            logger.error(f"{method} {url} - ERROR - {latency:.2f}s - {str(e)}")
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        avg_latency = self.total_latency / self.request_count if self.request_count > 0 else 0
        error_rate = self.error_count / self.request_count if self.request_count > 0 else 0
        
        return {
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': error_rate,
            'average_latency': avg_latency,
            'total_latency': self.total_latency
        }


# Global API client instance
api_client = APIClient()