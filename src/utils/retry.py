import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Any, Type, Tuple

import httpx

logger = logging.getLogger(__name__)


def retry_on_failure(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    multiplier: float = 2.0,
    retry_on: Tuple[Type[Exception], ...] = (httpx.HTTPStatusError, httpx.RequestError),
    retry_on_status: Tuple[int, ...] = (429, 500, 502, 503, 504)
) -> Callable:
    """Decorator for retrying function calls with exponential backoff."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                
                except retry_on as e:
                    last_exception = e
                    
                    # Check if we should retry based on status code
                    if hasattr(e, "response") and e.response is not None:
                        if e.response.status_code not in retry_on_status:
                            logger.error(f"Non-retryable status code {e.response.status_code}: {e}")
                            raise
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {delay:.1f} seconds..."
                        )
                        await asyncio.sleep(delay)
                        delay *= multiplier
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed. Last error: {e}")
                        raise
                
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except retry_on as e:
                    last_exception = e
                    
                    # Check if we should retry based on status code
                    if hasattr(e, "response") and e.response is not None:
                        if e.response.status_code not in retry_on_status:
                            logger.error(f"Non-retryable status code {e.response.status_code}: {e}")
                            raise
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {delay:.1f} seconds..."
                        )
                        time.sleep(delay)
                        delay *= multiplier
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed. Last error: {e}")
                        raise
                
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator