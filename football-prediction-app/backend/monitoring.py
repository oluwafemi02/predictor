"""
Monitoring and health check utilities for production deployment
"""

import time
import psutil
import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from flask import g, request, Response
import json
from models import db
from sqlalchemy import text
import redis
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class MetricData:
    """Data class for metrics"""
    timestamp: datetime
    endpoint: str
    method: str
    response_time: float
    status_code: int
    user_id: Optional[int] = None
    error: Optional[str] = None


class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.metrics_buffer = []
        self.buffer_size = 100
    
    def track_request(self, func: Callable) -> Callable:
        """Decorator to track request performance"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            g.start_time = start_time
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate response time
                response_time = time.time() - start_time
                
                # Extract status code
                if isinstance(result, tuple):
                    response, status_code = result[0], result[1]
                else:
                    response, status_code = result, 200
                
                # Record metric
                self.record_metric(
                    endpoint=request.endpoint or 'unknown',
                    method=request.method,
                    response_time=response_time,
                    status_code=status_code
                )
                
                return result
                
            except Exception as e:
                response_time = time.time() - start_time
                self.record_metric(
                    endpoint=request.endpoint or 'unknown',
                    method=request.method,
                    response_time=response_time,
                    status_code=500,
                    error=str(e)
                )
                raise
        
        return wrapper
    
    def record_metric(self, endpoint: str, method: str, response_time: float, 
                     status_code: int, error: Optional[str] = None):
        """Record a performance metric"""
        metric = MetricData(
            timestamp=datetime.utcnow(),
            endpoint=endpoint,
            method=method,
            response_time=response_time,
            status_code=status_code,
            user_id=getattr(g, 'user_id', None),
            error=error
        )
        
        # Add to buffer
        self.metrics_buffer.append(metric)
        
        # Flush to Redis if buffer is full
        if len(self.metrics_buffer) >= self.buffer_size:
            self.flush_metrics()
    
    def flush_metrics(self):
        """Flush metrics buffer to Redis"""
        if not self.redis_client or not self.metrics_buffer:
            return
        
        try:
            pipe = self.redis_client.pipeline()
            
            for metric in self.metrics_buffer:
                # Store in sorted set by timestamp
                key = f"metrics:{metric.endpoint}:{metric.timestamp.strftime('%Y%m%d')}"
                pipe.zadd(
                    key,
                    {json.dumps(asdict(metric), default=str): metric.timestamp.timestamp()}
                )
                pipe.expire(key, 86400 * 7)  # Keep for 7 days
                
                # Update aggregated stats
                stats_key = f"stats:{metric.endpoint}"
                pipe.hincrby(stats_key, "total_requests", 1)
                pipe.hincrbyfloat(stats_key, "total_response_time", metric.response_time)
                pipe.hincrby(stats_key, f"status_{metric.status_code}", 1)
                if metric.error:
                    pipe.hincrby(stats_key, "errors", 1)
            
            pipe.execute()
            self.metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush metrics: {str(e)}")
    
    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get aggregated statistics for an endpoint"""
        if not self.redis_client:
            return {}
        
        try:
            stats_key = f"stats:{endpoint}"
            stats = self.redis_client.hgetall(stats_key)
            
            if not stats:
                return {}
            
            total_requests = int(stats.get(b'total_requests', 0))
            total_response_time = float(stats.get(b'total_response_time', 0))
            errors = int(stats.get(b'errors', 0))
            
            return {
                'endpoint': endpoint,
                'total_requests': total_requests,
                'average_response_time': total_response_time / total_requests if total_requests > 0 else 0,
                'error_rate': (errors / total_requests * 100) if total_requests > 0 else 0,
                'status_codes': {
                    k.decode().replace('status_', ''): int(v) 
                    for k, v in stats.items() 
                    if k.decode().startswith('status_')
                }
            }
        except Exception as e:
            logger.error(f"Failed to get endpoint stats: {str(e)}")
            return {}


class HealthChecker:
    """Comprehensive health checking system"""
    
    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            result = db.session.execute(text('SELECT 1'))
            db.session.commit()
            
            # Check table count
            table_count = db.session.execute(
                text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            ).scalar()
            
            # Check connection pool
            engine = db.engine
            pool = engine.pool
            
            return {
                'status': 'healthy',
                'response_time': time.time() - start_time,
                'table_count': table_count,
                'connection_pool': {
                    'size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow()
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': time.time() - start_time
            }
    
    @staticmethod
    def check_redis(redis_url: str) -> Dict[str, Any]:
        """Check Redis connectivity"""
        start_time = time.time()
        
        try:
            r = redis.from_url(redis_url)
            r.ping()
            
            # Get memory info
            info = r.info('memory')
            
            return {
                'status': 'healthy',
                'response_time': time.time() - start_time,
                'memory': {
                    'used_memory_human': info.get('used_memory_human', 'N/A'),
                    'used_memory_peak_human': info.get('used_memory_peak_human', 'N/A'),
                    'mem_fragmentation_ratio': info.get('mem_fragmentation_ratio', 'N/A')
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': time.time() - start_time
            }
    
    @staticmethod
    def check_system_resources() -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'status': 'healthy',
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'percent': memory.percent,
                    'available': f"{memory.available / (1024**3):.2f} GB",
                    'total': f"{memory.total / (1024**3):.2f} GB"
                },
                'disk': {
                    'percent': disk.percent,
                    'free': f"{disk.free / (1024**3):.2f} GB",
                    'total': f"{disk.total / (1024**3):.2f} GB"
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def check_external_apis(api_endpoints: Dict[str, str]) -> Dict[str, Any]:
        """Check external API connectivity"""
        import requests
        results = {}
        
        for name, url in api_endpoints.items():
            start_time = time.time()
            
            try:
                response = requests.get(url, timeout=5)
                results[name] = {
                    'status': 'healthy' if response.status_code < 400 else 'degraded',
                    'status_code': response.status_code,
                    'response_time': time.time() - start_time
                }
            except Exception as e:
                results[name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'response_time': time.time() - start_time
                }
        
        return results
    
    @staticmethod
    def get_full_health_status(config: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive health status"""
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # Database check
        health_status['checks']['database'] = HealthChecker.check_database()
        
        # Redis check
        if config.get('REDIS_URL'):
            health_status['checks']['redis'] = HealthChecker.check_redis(config['REDIS_URL'])
        
        # System resources
        health_status['checks']['system'] = HealthChecker.check_system_resources()
        
        # External APIs
        if config.get('API_ENDPOINTS'):
            health_status['checks']['external_apis'] = HealthChecker.check_external_apis(
                config['API_ENDPOINTS']
            )
        
        # Determine overall status
        for check_name, check_result in health_status['checks'].items():
            if check_result.get('status') == 'unhealthy':
                health_status['overall_status'] = 'unhealthy'
                break
            elif check_result.get('status') == 'degraded':
                health_status['overall_status'] = 'degraded'
        
        return health_status


def setup_monitoring(app):
    """Set up monitoring for Flask app"""
    # Initialize performance monitor
    redis_url = app.config.get('REDIS_URL')
    redis_client = None
    
    if redis_url:
        try:
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis not available for monitoring: {str(e)}")
    
    monitor = PerformanceMonitor(redis_client)
    
    # Add before/after request handlers
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response: Response) -> Response:
        # Skip monitoring for static files and health checks
        if request.endpoint in ['static', 'health', 'health_detailed']:
            return response
        
        # Add response time header
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            response.headers['X-Response-Time'] = f"{response_time:.3f}"
        
        return response
    
    # Add health check endpoints
    @app.route('/health')
    def health():
        """Basic health check endpoint"""
        db_status = 'unknown'
        db_error = None
        
        try:
            # Test database connection
            from sqlalchemy import text
            from models import db
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            db_status = 'connected'
        except Exception as e:
            db_status = 'disconnected'
            db_error = str(e)
            
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'environment': app.config.get('ENV', 'production'),
            'database': {
                'status': db_status,
                'error': db_error,
                'uri_configured': bool(app.config.get('SQLALCHEMY_DATABASE_URI')),
                'is_postgresql': 'postgresql' in str(app.config.get('SQLALCHEMY_DATABASE_URI', ''))
            },
            'api_key_configured': bool(app.config.get('FOOTBALL_API_KEY'))
        }
    
    @app.route('/health/detailed')
    def health_detailed():
        """Detailed health check endpoint"""
        config = {
            'REDIS_URL': app.config.get('REDIS_URL'),
            'API_ENDPOINTS': {
                'sportmonks': 'https://api.sportmonks.com/v3/football/status',
                'rapidapi': 'https://api-football-v1.p.rapidapi.com/v2/status'
            }
        }
        
        health_status = HealthChecker.get_full_health_status(config)
        
        # Return appropriate status code
        if health_status['overall_status'] == 'unhealthy':
            return health_status, 503
        elif health_status['overall_status'] == 'degraded':
            return health_status, 200
        else:
            return health_status, 200
    
    @app.route('/metrics')
    def metrics():
        """Endpoint for Prometheus-style metrics"""
        # This could be expanded to export Prometheus format metrics
        return {
            'message': 'Metrics endpoint - integrate with Prometheus/Grafana for full metrics'
        }
    
    app.monitor = monitor
    
    return monitor