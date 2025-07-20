import random
import time
from typing import List, Optional, Tuple
from utils.WaitUtils import RobustWaitUtils
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import logging
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ElementUtils:
    """Generic element interaction utilities with robust retry mechanisms."""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.robust_wait = RobustWaitUtils(driver)
    
    def find_element_with_fallback(self, selectors: List[Tuple[str, str]], timeout: int = 10) -> Optional[WebElement]:
        """Find element using multiple selectors as fallback with robust waiting."""
        for by_method, selector in selectors:
            try:
                # First wait for page to be stable
                self.robust_wait.wait_for_page_load(min(timeout, 5))
                
                # Wait for element to be stable before interacting
                element = self.robust_wait.wait_for_element_stable(by_method, selector, timeout=timeout)
                if element:
                    logger.info(f"Found stable element with selector: {by_method}={selector}")
                    return element
                
                # Fallback to standard wait if stability check fails
                element = self.wait.until(EC.presence_of_element_located((by_method, selector)))
                logger.info(f"Found element with selector: {by_method}={selector}")
                return element
            except TimeoutException:
                continue
        logger.warning(f"Element not found with any selector: {selectors}")
        return None
    
    def find_clickable_element(self, selectors: List[Tuple[str, str]], timeout: int = 10) -> Optional[WebElement]:
        """Find clickable element using multiple selectors as fallback with robust waiting."""
        for by_method, selector in selectors:
            try:
                # First wait for page to be stable
                self.robust_wait.wait_for_page_load(min(timeout, 5))
                
                # Wait for element to be stable and clickable
                element = self.robust_wait.wait_for_element_stable(by_method, selector, timeout=timeout)
                if element and element.is_enabled():
                    logger.info(f"Found stable clickable element with selector: {by_method}={selector}")
                    return element
                
                # Fallback to standard wait if stability check fails
                element = self.wait.until(EC.element_to_be_clickable((by_method, selector)))
                logger.info(f"Found clickable element with selector: {by_method}={selector}")
                return element
            except TimeoutException:
                continue
        logger.warning(f"Clickable element not found with any selector: {selectors}")
        return None
    
    def click_element(self, element: WebElement, verify_click: bool = True, 
                     verification_url: str = None, verification_title: str = None, 
                     max_retries: int = 3) -> bool:
        """Click element with robust retry mechanism and verification."""
        for attempt in range(max_retries):
            try:
                current_url = self.driver.current_url
                current_title = self.driver.title
                
                # Scroll element into view if needed
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                
                # Add small random delay to avoid being detected as bot
                time.sleep(random.uniform(0.1, 0.3))
                
                # Try different click methods
                click_success = False
                
                # Method 1: Standard click
                try:
                    element.click()
                    click_success = True
                    logger.info("Element clicked successfully (standard method)")
                except Exception as click_error:
                    logger.warning(f"Standard click failed: {click_error}")
                    
                    # Method 2: JavaScript click
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        click_success = True
                        logger.info("Element clicked successfully (JavaScript method)")
                    except Exception as js_click_error:
                        logger.warning(f"JavaScript click failed: {js_click_error}")
                        
                        # Method 3: Action chains
                        try:
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(self.driver)
                            actions.move_to_element(element).click().perform()
                            click_success = True
                            logger.info("Element clicked successfully (ActionChains method)")
                        except Exception as action_error:
                            logger.warning(f"ActionChains click failed: {action_error}")
                
                if not click_success:
                    raise Exception("All click methods failed")
                
                if verify_click:
                    # Wait for page transition
                    if self.robust_wait.wait_for_page_transition(current_url, timeout=10):
                        logger.info("Click verified successful - page transition detected")
                        return True
                    
                    # Fallback verification
                    time.sleep(2)
                    if (verification_url and self.driver.current_url != verification_url) or \
                       (verification_title and verification_title not in self.driver.title) or \
                       (not verification_url and not verification_title and 
                        (self.driver.current_url != current_url or current_title != self.driver.title)):
                        logger.info("Click verified successful - page changed")
                        return True
                    else:
                        logger.warning(f"Click attempt {attempt + 1} reported success but page didn't change")
                        if attempt < max_retries - 1:
                            time.sleep(1)  # Wait before retry
                            continue
                        return False
                return True
                
            except Exception as e:
                logger.error(f"Click attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                    continue
                return False
        
        return False
    
    def fill_input_field(self, element: WebElement, value: str, clear_first: bool = True, 
                        max_retries: int = 3) -> bool:
        """Fill input field with robust retry mechanism."""
        for attempt in range(max_retries):
            try:
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                
                # Wait for element to be ready
                time.sleep(random.uniform(0.1, 0.3))
                
                # Clear field if requested
                if clear_first:
                    element.clear()
                    time.sleep(0.1)  # Small delay after clear
                
                # Fill field with random delays between characters (more human-like)
                for char in value:
                    element.send_keys(char)
                    time.sleep(random.uniform(0.01, 0.05))  # Random delay between characters
                
                logger.info(f"Filled input field with value: {value[:10]}...")
                return True
                
            except Exception as e:
                logger.error(f"Fill attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                    continue
                return False
        
        return False
    
    def submit_form(self, element: WebElement, max_retries: int = 3) -> bool:
        """Submit form by sending RETURN key with retry mechanism."""
        for attempt in range(max_retries):
            try:
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                
                # Small delay before submitting
                time.sleep(random.uniform(0.1, 0.3))
                
                element.send_keys(Keys.RETURN)
                logger.info("Form submitted with RETURN key")
                return True
                
            except Exception as e:
                logger.error(f"Submit attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                    continue
                return False
        
        return False
    
    def find_elements_by_text_pattern(self, text_patterns: List[str]) -> List[WebElement]:
        """Find elements containing any of the specified text patterns."""
        elements = []
        for pattern in text_patterns:
            try:
                found = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{pattern}')]")
                elements.extend(found)
            except Exception as e:
                logger.warning(f"Error finding elements with pattern '{pattern}': {e}")
        return elements
    
    def click_dialog_button(self, button_text: str, timeout: int = 10) -> bool:
        """Click a button in a dialog by text content."""
        try:
            # Wait for dialog to be present
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog'] | //mat-dialog-container"))
            )
            
            # Try multiple selectors for dialog buttons
            button_selectors = [
                (By.XPATH, f"//button[contains(text(), '{button_text}')]"),
                (By.XPATH, f"//mat-dialog-container//button[contains(text(), '{button_text}')]"),
                (By.XPATH, f"//div[@role='dialog']//button[contains(text(), '{button_text}')]"),
                (By.XPATH, f"//app-work-order-action-dialog//button[contains(text(), '{button_text}')]"),
                (By.XPATH, f"//button[contains(@class, 'btn-primary') and contains(text(), '{button_text}')]"),
                (By.XPATH, f"//button[contains(@class, 'btn-success') and contains(text(), '{button_text}')]")
            ]
            
            button = None
            for selector in button_selectors:
                try:
                    button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    logger.info(f"Found dialog button '{button_text}' with selector: {selector[1]}")
                    break
                except Exception:
                    continue
            
            if not button:
                logger.error(f"Dialog button '{button_text}' not found")
                return False
            
            # Scroll button into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(1)
            
            # Try multiple click methods
            click_success = False
            
            # Method 1: Native click
            try:
                button.click()
                click_success = True
                logger.info(f"Dialog button '{button_text}' clicked using native click")
            except Exception as e:
                logger.warning(f"Native click failed: {e}")
            
            # Method 2: JavaScript click
            if not click_success:
                try:
                    self.driver.execute_script("arguments[0].click();", button)
                    click_success = True
                    logger.info(f"Dialog button '{button_text}' clicked using JavaScript")
                except Exception as e:
                    logger.warning(f"JavaScript click failed: {e}")
            
            # Method 3: ActionChains
            if not click_success:
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(self.driver)
                    actions.move_to_element(button).click().perform()
                    click_success = True
                    logger.info(f"Dialog button '{button_text}' clicked using ActionChains")
                except Exception as e:
                    logger.warning(f"ActionChains click failed: {e}")
            
            return click_success
            
        except Exception as e:
            logger.error(f"Failed to click dialog button '{button_text}': {e}")
            return False
