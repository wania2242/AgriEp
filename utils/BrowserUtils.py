from utils.WaitUtils import RobustWaitUtils
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import logging
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BrowserUtils:
    """Generic browser utility functions for navigation and window management."""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.robust_wait = RobustWaitUtils(driver)
    
    def navigate_to_url(self, url: str, timeout: int = 10) -> bool:
        """Navigate to a URL with error handling and robust page load waiting."""
        try:
            self.driver.get(url)
            logger.info(f"Successfully navigated to: {url}")
            
            # Wait for page to be fully loaded
            self.robust_wait.wait_for_page_load(timeout)
            
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return False
    
    def wait_for_url_contains(self, url_part: str, timeout: int = 10) -> bool:
        """Wait for URL to contain specific text."""
        try:
            self.wait.until(EC.url_contains(url_part))
            logger.info(f"URL now contains: {url_part}")
            return True
        except TimeoutException:
            logger.warning(f"URL did not contain '{url_part}' within {timeout} seconds")
            return False
    
    def switch_to_new_window(self, original_handle: str, timeout: int = 10) -> bool:
        """Switch to a new window that opened after the original handle."""
        try:
            self.wait.until(lambda d: len(d.window_handles) > 1)
            for handle in self.driver.window_handles:
                if handle != original_handle:
                    self.driver.switch_to.window(handle)
                    logger.info(f"Switched to new window: {self.driver.current_url}")
                    return True
            return False
        except TimeoutException:
            logger.warning("No new window opened within timeout")
            return False
    
    def switch_to_window_by_url_contains(self, url_part: str) -> bool:
        """Switch to window containing specific URL part."""
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if url_part in self.driver.current_url:
                logger.info(f"Switched to window with URL containing: {url_part}")
                return True
        return False
    
    def save_screenshot(self, filename: str) -> bool:
        """Save screenshot for debugging."""
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save screenshot {filename}: {e}")
            return False
    
    def save_page_source(self, filename: str) -> bool:
        """Save page source for debugging."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logger.info(f"Page source saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save page source {filename}: {e}")
            return False
