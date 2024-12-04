"""Retry decorator for handling transient failures."""

import time
import logging
from functools import wraps
from typing import Type, Tuple, Callable, Any, Optional

logger = logging.getLogger(__name__)

def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger: Optional[logging.Logger] = None
) -> Callable:
    """Decorator that retries a function on specified exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exception types to catch and retry on
        logger: Optional logger instance for retry attempts
        
    Returns:
        Callable: Decorated function that implements retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        if logger:
                            logger.warning(
                                f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                                f"Retrying in {delay} seconds..."
                            )
                        time.sleep(delay)
                    else:
                        if logger:
                            logger.error(
                                f"All {max_retries} retry attempts failed. "
                                f"Last error: {str(e)}"
                            )
                        raise last_exception
                        
            return None  # Should never reach here
            
        return wrapper
    return decorator