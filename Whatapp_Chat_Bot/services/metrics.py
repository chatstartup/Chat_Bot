"""Metrics collection using Prometheus"""
import time
import logging
from functools import wraps
from typing import Callable
from prometheus_client import Counter, Histogram, Gauge, Info
from config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Define metrics
REQUEST_COUNT = Counter(
    'chatbot_requests_total',
    'Total number of requests',
    ['endpoint', 'method', 'status']
)

REQUEST_LATENCY = Histogram(
    'chatbot_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint']
)

ACTIVE_SESSIONS = Gauge(
    'chatbot_active_sessions',
    'Number of active chat sessions'
)

ERROR_COUNT = Counter(
    'chatbot_errors_total',
    'Total number of errors',
    ['type']
)

RATE_LIMIT_COUNT = Counter(
    'chatbot_rate_limits_total',
    'Total number of rate limit hits',
    ['client_ip']
)

API_LATENCY = Histogram(
    'chatbot_external_api_latency_seconds',
    'External API latency in seconds',
    ['service']
)

CACHE_HITS = Counter(
    'chatbot_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'chatbot_cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

VECTOR_DB_OPERATIONS = Counter(
    'chatbot_vectordb_operations_total',
    'Total number of vector database operations',
    ['operation']
)

# System info
SYSTEM_INFO = Info('chatbot_system', 'System information')
SYSTEM_INFO.info({
    'version': '1.0.0',
    'python_version': '3.11',
    'environment': settings.ENVIRONMENT
})

def track_request_metrics(endpoint: str) -> Callable:
    """Track request metrics"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapped(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                ERROR_COUNT.labels(type=type(e).__name__).inc()
                raise
            finally:
                REQUEST_COUNT.labels(
                    endpoint=endpoint,
                    method=f.__name__,
                    status=status
                ).inc()
                
                REQUEST_LATENCY.labels(endpoint=endpoint).observe(
                    time.time() - start_time
                )
        return wrapped
    return decorator

def track_api_latency(service: str) -> Callable:
    """Track external API latency"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        async def wrapped(*args, **kwargs):
            start_time = time.time()
            try:
                result = await f(*args, **kwargs)
                API_LATENCY.labels(service=service).observe(
                    time.time() - start_time
                )
                return result
            except Exception as e:
                ERROR_COUNT.labels(type=type(e).__name__).inc()
                raise
        return wrapped
    return decorator

def track_cache_metrics(cache_type: str) -> Callable:
    """Track cache hits and misses"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        async def wrapped(*args, **kwargs):
            try:
                result = await f(*args, **kwargs)
                if result is not None:
                    CACHE_HITS.labels(cache_type=cache_type).inc()
                else:
                    CACHE_MISSES.labels(cache_type=cache_type).inc()
                return result
            except Exception as e:
                ERROR_COUNT.labels(type=type(e).__name__).inc()
                raise
        return wrapped
    return decorator

def track_vectordb_operation(operation: str) -> Callable:
    """Track vector database operations"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        async def wrapped(*args, **kwargs):
            try:
                result = await f(*args, **kwargs)
                VECTOR_DB_OPERATIONS.labels(operation=operation).inc()
                return result
            except Exception as e:
                ERROR_COUNT.labels(type=type(e).__name__).inc()
                raise
        return wrapped
    return decorator

def update_active_sessions(delta: int = 1) -> None:
    """Update number of active sessions"""
    ACTIVE_SESSIONS.inc(delta)

def record_rate_limit(client_ip: str) -> None:
    """Record rate limit hit"""
    RATE_LIMIT_COUNT.labels(client_ip=client_ip).inc()
