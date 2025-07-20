import logging
import random
import time
from typing import Callable
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RetryMechanism:
    """Generic retry mechanism for operations that might fail due to timing issues."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def execute_with_retry(self, operation: Callable, operation_name: str = "operation", 
                          success_condition: Callable = None) -> bool:
        """Execute an operation with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                result = operation()
                
                # Check success condition if provided
                if success_condition and not success_condition():
                    raise Exception(f"Success condition not met for {operation_name}")
                
                logger.info(f"{operation_name} completed successfully on attempt {attempt + 1}")
                return True
                
            except Exception as e:
                logger.warning(f"{operation_name} attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff with jitter
                    delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                    logger.info(f"Retrying {operation_name} in {delay:.2f} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"{operation_name} failed after {self.max_retries} attempts")
                    return False
        
        return False
