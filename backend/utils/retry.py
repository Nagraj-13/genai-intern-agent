import asyncio
import logging
import random
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class RetryError(Exception):
    """Error raised when all retry attempts are exhausted"""
    def __init__(self, message: str, last_exception: Exception):
        super().__init__(message)
        self.last_exception = last_exception

async def retry_with_exponential_backoff(
    func: Callable,
    *args,
    max_retries: int = 1,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_exceptions: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Retry a function with exponential backoff strategy.
    
    Args:
        func: The async function to retry
        *args: Arguments to pass to the function
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for the first retry
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to prevent thundering herd
        retry_exceptions: Tuple of exceptions that should trigger a retry
        **kwargs: Keyword arguments to pass to the function
    
    Returns:
        Result of the successful function call
        
    Raises:
        RetryError: When all retry attempts are exhausted
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):  # +1 for initial attempt
        try:
            logger.info(f"Executing {func.__name__} (attempt {attempt + 1}/{max_retries + 1})")
            result = await func(*args, **kwargs)
            
            if attempt > 0:
                logger.info(f"{func.__name__} succeeded after {attempt} retries")
            
            return result
            
        except retry_exceptions as e:
            last_exception = e
            
            # If this was the last attempt, raise the error
            if attempt == max_retries:
                logger.error(f"{func.__name__} failed after {max_retries + 1} attempts: {str(e)}")
                break
            
            # Calculate delay for next attempt
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            
            # Add jitter to prevent thundering herd problem
            if jitter:
                delay = delay * (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
            
            logger.warning(
                f"{func.__name__} attempt {attempt + 1} failed: {str(e)}. "
                f"Retrying in {delay:.2f} seconds..."
            )
            
            await asyncio.sleep(delay)
        
        except Exception as e:
            # Non-retryable exception
            logger.error(f"{func.__name__} failed with non-retryable exception: {str(e)}")
            raise
    
    # All retries exhausted
    raise RetryError(
        f"Function {func.__name__} failed after {max_retries + 1} attempts",
        last_exception
    )

def retry_async(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_exceptions: tuple = (Exception,)
):
    """
    Decorator for async functions that adds retry logic with exponential backoff.
    
    Usage:
        @retry_async(max_retries=3, base_delay=1.0)
        async def my_function():
            # Function that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_exponential_backoff(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter,
                retry_exceptions=retry_exceptions,
                **kwargs
            )
        return wrapper
    return decorator

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for failing fast when services are down.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open, requests fail immediately
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self