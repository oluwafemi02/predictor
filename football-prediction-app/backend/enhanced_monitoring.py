"""
Enhanced Monitoring System for Football Prediction App
Tracks prediction accuracy, API performance, and system health
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from functools import wraps
from collections import defaultdict, deque
from flask import g, request, Response, current_app
from sqlalchemy import text
import redis
import psutil
import os

logger = logging.getLogger(__name__)


@dataclass
class PredictionMetrics:
    """Metrics for prediction accuracy tracking"""
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy_by_confidence: Dict[str, float] = field(default_factory=dict)
    accuracy_by_league: Dict[str, float] = field(default_factory=dict)
    accuracy_by_outcome: Dict[str, float] = field(default_factory=dict)
    
    @property
    def overall_accuracy(self) -> float:
        """Calculate overall prediction accuracy"""
        if self.total_predictions == 0:
            return 0.0
        return (self.correct_predictions / self.total_predictions) * 100
    
    def update(self, prediction_outcome: str, actual_outcome: str, 
               confidence: float, league: str):
        """Update metrics with new prediction result"""
        self.total_predictions += 1
        is_correct = prediction_outcome == actual_outcome
        
        if is_correct:
            self.correct_predictions += 1
        
        # Update accuracy by confidence level
        confidence_bucket = f"{int(confidence // 10) * 10}-{int(confidence // 10) * 10 + 10}%"
        if confidence_bucket not in self.accuracy_by_confidence:
            self.accuracy_by_confidence[confidence_bucket] = {'correct': 0, 'total': 0}
        self.accuracy_by_confidence[confidence_bucket]['total'] += 1
        if is_correct:
            self.accuracy_by_confidence[confidence_bucket]['correct'] += 1
        
        # Update accuracy by league
        if league not in self.accuracy_by_league:
            self.accuracy_by_league[league] = {'correct': 0, 'total': 0}
        self.accuracy_by_league[league]['total'] += 1
        if is_correct:
            self.accuracy_by_league[league]['correct'] += 1
        
        # Update accuracy by outcome type
        if prediction_outcome not in self.accuracy_by_outcome:
            self.accuracy_by_outcome[prediction_outcome] = {'correct': 0, 'total': 0}
        self.accuracy_by_outcome[prediction_outcome]['total'] += 1
        if is_correct:
            self.accuracy_by_outcome[prediction_outcome]['correct'] += 1


@dataclass
class APIMetrics:
    """Metrics for API performance tracking"""
    total_requests: int = 0
    total_errors: int = 0
    average_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    endpoints_stats: Dict[str, Dict] = field(default_factory=dict)
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    
    def update(self, endpoint: str, method: str, response_time: float, 
               status_code: int):
        """Update API metrics"""
        self.total_requests += 1
        self.response_times.append(response_time)
        self.average_response_time = sum(self.response_times) / len(self.response_times)
        self.status_codes[status_code] += 1
        
        if status_code >= 400:
            self.total_errors += 1
        
        # Update endpoint-specific stats
        key = f"{method} {endpoint}"
        if key not in self.endpoints_stats:
            self.endpoints_stats[key] = {
                'count': 0,
                'total_time': 0,
                'errors': 0,
                'avg_time': 0
            }
        
        stats = self.endpoints_stats[key]
        stats['count'] += 1
        stats['total_time'] += response_time
        stats['avg_time'] = stats['total_time'] / stats['count']
        if status_code >= 400:
            stats['errors'] += 1


class EnhancedMonitor:
    """Enhanced monitoring system with comprehensive tracking"""
    
    def __init__(self, app=None, redis_client=None):
        self.app = app
        self.redis_client = redis_client
        self.prediction_metrics = PredictionMetrics()
        self.api_metrics = APIMetrics()
        self.start_time = datetime.utcnow()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize monitoring with Flask app"""
        self.app = app
        app.monitor = self
        
        # Add before/after request handlers
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        # Add monitoring endpoints
        self._register_monitoring_endpoints()
        
        logger.info("Enhanced monitoring initialized")
    
    def _before_request(self):
        """Track request start time"""
        g.start_time = time.time()
        g.request_id = request.headers.get('X-Request-ID', 
                                          f"{time.time()}-{request.remote_addr}")
    
    def _after_request(self, response):
        """Track request completion"""
        if hasattr(g, 'start_time'):
            response_time = (time.time() - g.start_time) * 1000  # Convert to ms
            
            # Update API metrics
            endpoint = request.endpoint or 'unknown'
            self.api_metrics.update(
                endpoint=endpoint,
                method=request.method,
                response_time=response_time,
                status_code=response.status_code
            )
            
            # Log slow requests
            if response_time > 1000:  # More than 1 second
                logger.warning(f"Slow request: {request.method} {request.path} "
                             f"took {response_time:.2f}ms")
            
            # Store metrics in Redis if available
            if self.redis_client:
                try:
                    self._store_metrics_in_redis(endpoint, response_time, 
                                               response.status_code)
                except Exception as e:
                    logger.error(f"Failed to store metrics in Redis: {str(e)}")
        
        return response
    
    def _register_monitoring_endpoints(self):
        """Register monitoring endpoints"""
        
        @self.app.route('/api/monitoring/health')
        def health_check():
            """Comprehensive health check"""
            health = self.get_health_status()
            status_code = 200 if health['status'] == 'healthy' else 503
            return json.dumps(health), status_code
        
        @self.app.route('/api/monitoring/metrics')
        def metrics():
            """Get current metrics"""
            return json.dumps(self.get_metrics())
        
        @self.app.route('/api/monitoring/prediction-accuracy')
        def prediction_accuracy():
            """Get prediction accuracy metrics"""
            return json.dumps(self.get_prediction_accuracy())
        
        @self.app.route('/api/monitoring/api-stats')
        def api_stats():
            """Get API performance statistics"""
            return json.dumps(self.get_api_stats())
    
    def track_prediction(self, match_id: int, predicted_outcome: str, 
                        actual_outcome: str, confidence: float, 
                        league: str = "Unknown"):
        """Track prediction accuracy"""
        self.prediction_metrics.update(
            prediction_outcome=predicted_outcome,
            actual_outcome=actual_outcome,
            confidence=confidence,
            league=league
        )
        
        # Store in Redis for persistence
        if self.redis_client:
            key = f"prediction_result:{match_id}"
            data = {
                'predicted': predicted_outcome,
                'actual': actual_outcome,
                'confidence': confidence,
                'league': league,
                'timestamp': datetime.utcnow().isoformat()
            }
            self.redis_client.setex(key, 86400 * 30, json.dumps(data))  # 30 days
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': str(datetime.utcnow() - self.start_time),
            'checks': {}
        }
        
        # Database health
        try:
            db_health = self._check_database_health()
            health['checks']['database'] = db_health
            if db_health['status'] != 'healthy':
                health['status'] = 'degraded'
        except Exception as e:
            health['checks']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health['status'] = 'unhealthy'
        
        # Redis health
        if self.redis_client:
            try:
                redis_health = self._check_redis_health()
                health['checks']['redis'] = redis_health
                if redis_health['status'] != 'healthy':
                    health['status'] = 'degraded'
            except Exception as e:
                health['checks']['redis'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        # System resources
        health['checks']['system'] = self._check_system_resources()
        
        # API health
        health['checks']['api'] = {
            'status': 'healthy' if self.api_metrics.total_errors / max(self.api_metrics.total_requests, 1) < 0.05 else 'degraded',
            'error_rate': f"{(self.api_metrics.total_errors / max(self.api_metrics.total_requests, 1)) * 100:.2f}%",
            'avg_response_time': f"{self.api_metrics.average_response_time:.2f}ms"
        }
        
        return health
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': str(datetime.utcnow() - self.start_time),
            'api': {
                'total_requests': self.api_metrics.total_requests,
                'total_errors': self.api_metrics.total_errors,
                'error_rate': f"{(self.api_metrics.total_errors / max(self.api_metrics.total_requests, 1)) * 100:.2f}%",
                'average_response_time': f"{self.api_metrics.average_response_time:.2f}ms",
                'status_codes': dict(self.api_metrics.status_codes)
            },
            'predictions': {
                'total': self.prediction_metrics.total_predictions,
                'correct': self.prediction_metrics.correct_predictions,
                'accuracy': f"{self.prediction_metrics.overall_accuracy:.2f}%"
            },
            'system': self._check_system_resources()
        }
    
    def get_prediction_accuracy(self) -> Dict[str, Any]:
        """Get detailed prediction accuracy metrics"""
        accuracy_data = {
            'overall': {
                'total_predictions': self.prediction_metrics.total_predictions,
                'correct_predictions': self.prediction_metrics.correct_predictions,
                'accuracy': f"{self.prediction_metrics.overall_accuracy:.2f}%"
            },
            'by_confidence': {},
            'by_league': {},
            'by_outcome': {}
        }
        
        # Calculate accuracy by confidence
        for bucket, stats in self.prediction_metrics.accuracy_by_confidence.items():
            if stats['total'] > 0:
                accuracy_data['by_confidence'][bucket] = {
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'accuracy': f"{(stats['correct'] / stats['total']) * 100:.2f}%"
                }
        
        # Calculate accuracy by league
        for league, stats in self.prediction_metrics.accuracy_by_league.items():
            if stats['total'] > 0:
                accuracy_data['by_league'][league] = {
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'accuracy': f"{(stats['correct'] / stats['total']) * 100:.2f}%"
                }
        
        # Calculate accuracy by outcome type
        for outcome, stats in self.prediction_metrics.accuracy_by_outcome.items():
            if stats['total'] > 0:
                accuracy_data['by_outcome'][outcome] = {
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'accuracy': f"{(stats['correct'] / stats['total']) * 100:.2f}%"
                }
        
        return accuracy_data
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Get detailed API performance statistics"""
        stats = {
            'summary': {
                'total_requests': self.api_metrics.total_requests,
                'total_errors': self.api_metrics.total_errors,
                'error_rate': f"{(self.api_metrics.total_errors / max(self.api_metrics.total_requests, 1)) * 100:.2f}%",
                'average_response_time': f"{self.api_metrics.average_response_time:.2f}ms"
            },
            'endpoints': [],
            'slowest_endpoints': [],
            'most_errors': []
        }
        
        # Sort endpoints by various metrics
        endpoints_list = [
            {
                'endpoint': key,
                'count': value['count'],
                'avg_time': f"{value['avg_time']:.2f}ms",
                'errors': value['errors'],
                'error_rate': f"{(value['errors'] / value['count']) * 100:.2f}%"
            }
            for key, value in self.api_metrics.endpoints_stats.items()
        ]
        
        # Get top endpoints
        stats['endpoints'] = sorted(endpoints_list, key=lambda x: x['count'], reverse=True)[:10]
        stats['slowest_endpoints'] = sorted(endpoints_list, key=lambda x: float(x['avg_time'][:-2]), reverse=True)[:5]
        stats['most_errors'] = sorted(endpoints_list, key=lambda x: x['errors'], reverse=True)[:5]
        
        return stats
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        from models import db
        
        start_time = time.time()
        try:
            # Try a simple query
            result = db.session.execute(text('SELECT 1'))
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time': f"{response_time:.2f}ms"
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health"""
        start_time = time.time()
        try:
            self.redis_client.ping()
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time': f"{response_time:.2f}ms"
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        return {
            'cpu_percent': f"{psutil.cpu_percent(interval=0.1):.1f}%",
            'memory': {
                'percent': f"{psutil.virtual_memory().percent:.1f}%",
                'available': f"{psutil.virtual_memory().available / (1024**3):.2f}GB"
            },
            'disk': {
                'percent': f"{psutil.disk_usage('/').percent:.1f}%",
                'free': f"{psutil.disk_usage('/').free / (1024**3):.2f}GB"
            }
        }
    
    def _store_metrics_in_redis(self, endpoint: str, response_time: float, 
                               status_code: int):
        """Store metrics in Redis for time-series analysis"""
        timestamp = int(time.time())
        key = f"metrics:{endpoint}:{timestamp // 60}"  # Group by minute
        
        data = {
            'timestamp': timestamp,
            'response_time': response_time,
            'status_code': status_code
        }
        
        # Use Redis list to store time-series data
        self.redis_client.lpush(key, json.dumps(data))
        self.redis_client.expire(key, 86400)  # Keep for 24 hours


def track_performance(f):
    """Decorator to track function performance"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Log slow operations
            if execution_time > 500:  # More than 500ms
                logger.warning(f"Slow operation: {f.__name__} took {execution_time:.2f}ms")
            
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Error in {f.__name__} after {execution_time:.2f}ms: {str(e)}")
            raise
    
    return wrapper


def setup_monitoring(app):
    """Setup monitoring for the Flask app"""
    # Try to get Redis client
    redis_client = None
    redis_url = app.config.get('REDIS_URL')
    if redis_url:
        try:
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
            logger.info("Redis connected for monitoring")
        except Exception as e:
            logger.warning(f"Could not connect to Redis for monitoring: {str(e)}")
    
    # Initialize enhanced monitor
    monitor = EnhancedMonitor(app, redis_client)
    
    return monitor