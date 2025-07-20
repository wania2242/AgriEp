
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from typing import Optional
import time
import logging
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RobustWaitUtils:
    """Robust waiting utilities with intelligent retry mechanisms."""
    
    def __init__(self, driver, base_timeout: int = 30):
        self.driver = driver
        self.base_timeout = base_timeout
        self.wait = WebDriverWait(driver, base_timeout)
    
    def wait_for_page_load(self, timeout: int = None) -> bool:
        """Wait for page to be fully loaded with multiple indicators."""
        if timeout is None:
            timeout = self.base_timeout
        
        try:
            # Wait for document ready state
            self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            
            # Wait for jQuery to be ready (if present)
            try:
                self.wait.until(lambda d: d.execute_script("return jQuery.active == 0"))
            except:
                pass  # jQuery not present, continue
            
            # Wait for any ongoing AJAX requests to complete
            self.wait.until(lambda d: d.execute_script("return window.performance.getEntriesByType('resource').filter(r => r.initiatorType === 'xmlhttprequest').every(r => r.responseEnd > 0)"))
            
            logger.info("Page fully loaded")
            return True
        except TimeoutException:
            logger.warning("Page load timeout, but continuing")
            return False
    
    def wait_for_element_stable(self, by_method: str, selector: str, timeout: int = None, 
                               stability_duration: float = 1.0) -> Optional[WebElement]:
        """Wait for element to be stable (not moving/changing) before interacting."""
        if timeout is None:
            timeout = self.base_timeout
        
        start_time = time.time()
        last_position = None
        stable_start = None
        
        while time.time() - start_time < timeout:
            try:
                element = self.driver.find_element(by_method, selector)
                
                # Check if element is visible and enabled
                if not element.is_displayed() or not element.is_enabled():
                    time.sleep(0.5)
                    continue
                
                # Get current position
                current_position = element.location
                
                if last_position is None:
                    last_position = current_position
                    stable_start = time.time()
                elif current_position == last_position:
                    if stable_start is None:
                        stable_start = time.time()
                    elif time.time() - stable_start >= stability_duration:
                        logger.info(f"Element stable for {stability_duration}s: {by_method}={selector}")
                        return element
                else:
                    last_position = current_position
                    stable_start = None
                
                time.sleep(0.2)
            except (NoSuchElementException, StaleElementReferenceException):
                time.sleep(0.5)
                continue
        
        logger.warning(f"Element not stable within timeout: {by_method}={selector}")
        return None
    
    def wait_for_page_transition(self, initial_url: str = None, timeout: int = None) -> bool:
        """Wait for page transition to complete (URL change, loading indicators, etc.)."""
        if timeout is None:
            timeout = self.base_timeout
        
        if initial_url is None:
            initial_url = self.driver.current_url
        
        start_time = time.time()
        last_url = initial_url
        
        while time.time() - start_time < timeout:
            current_url = self.driver.current_url
            
            # Check if URL changed
            if current_url != last_url:
                logger.info(f"URL changed from {last_url} to {current_url}")
                # Wait a bit more for the new page to settle
                time.sleep(2)
                return True
            
            # Check for loading indicators
            try:
                loading_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "[class*='loading'], [class*='spinner'], [class*='progress'], [aria-busy='true']")
                if not loading_elements:
                    # No loading indicators, page might be ready
                    time.sleep(1)
                    if self.driver.current_url != current_url:
                        continue
                    return True
            except:
                pass
            
            time.sleep(0.5)
        
        logger.warning("Page transition timeout")
        return False
