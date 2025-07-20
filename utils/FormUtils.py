from typing import List, Tuple
from utils.ElementUtils import ElementUtils
from selenium.webdriver.common.by import By
import logging
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FormUtils:
    """Generic form filling utilities."""
    
    def __init__(self, driver):
        self.driver = driver
        self.element_utils = ElementUtils(driver)
    
    def fill_email_field(self, email: str, selectors: List[Tuple[str, str]] = None) -> bool:
        """Fill email field with generic selectors."""
        if selectors is None:
            selectors = [
                (By.ID, "i0116"),
                (By.CSS_SELECTOR, "input[name='loginfmt']"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[type='text']")
            ]
        
        email_input = self.element_utils.find_element_with_fallback(selectors, timeout=30)
        if not email_input:
            self._debug_input_elements()
            return False
        
        if not self.element_utils.fill_input_field(email_input, email):
            return False
        
        return self.element_utils.submit_form(email_input)
    
    def fill_password_field(self, password: str, selectors: List[Tuple[str, str]] = None) -> bool:
        """Fill password field with generic selectors."""
        if selectors is None:
            selectors = [
                (By.ID, "i0118"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[name='passwd']")
            ]
        
        password_input = self.element_utils.find_element_with_fallback(selectors, timeout=10)
        if not password_input:
            return False
        
        if not self.element_utils.fill_input_field(password_input, password):
            return False
        
        return self.element_utils.submit_form(password_input)
    
    def _debug_input_elements(self):
        """Debug helper to list all input elements on page."""
        try:
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            logger.info(f"Found {len(inputs)} input elements on page:")
            for inp in inputs:
                logger.info({
                    "id": inp.get_attribute("id"),
                    "name": inp.get_attribute("name"),
                    "type": inp.get_attribute("type"),
                    "placeholder": inp.get_attribute("placeholder")
                })
        except Exception as e:
            logger.error(f"Error listing input elements: {e}")