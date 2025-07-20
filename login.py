from shared_driver import get_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import os
import pickle
import datetime
import json
import shutil
import pyotp
from dotenv import load_dotenv
from typing import Optional, List, Tuple, Dict, Any, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()


class BrowserUtils:
    """Generic browser utility functions for navigation and window management."""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    def navigate_to_url(self, url: str, timeout: int = 10) -> bool:
        """Navigate to a URL with error handling."""
        try:
            self.driver.get(url)
            logger.info(f"Successfully navigated to: {url}")
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


class ElementUtils:
    """Generic element interaction utilities."""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    def find_element_with_fallback(self, selectors: List[Tuple[str, str]], timeout: int = 10) -> Optional[WebElement]:
        """Find element using multiple selectors as fallback."""
        for by_method, selector in selectors:
            try:
                element = self.wait.until(EC.presence_of_element_located((by_method, selector)))
                logger.info(f"Found element with selector: {by_method}={selector}")
                return element
            except TimeoutException:
                continue
        logger.warning(f"Element not found with any selector: {selectors}")
        return None
    
    def find_clickable_element(self, selectors: List[Tuple[str, str]], timeout: int = 10) -> Optional[WebElement]:
        """Find clickable element using multiple selectors as fallback."""
        for by_method, selector in selectors:
            try:
                element = self.wait.until(EC.element_to_be_clickable((by_method, selector)))
                logger.info(f"Found clickable element with selector: {by_method}={selector}")
                return element
            except TimeoutException:
                continue
        logger.warning(f"Clickable element not found with any selector: {selectors}")
        return None
    
    def click_element(self, element: WebElement, verify_click: bool = True, 
                     verification_url: str = None, verification_title: str = None) -> bool:
        """Click element with optional verification."""
        try:
            current_url = self.driver.current_url
            current_title = self.driver.title
            
            element.click()
            logger.info("Element clicked successfully")
            
            if verify_click:
                time.sleep(2)  # Wait for potential changes
                if (verification_url and self.driver.current_url != verification_url) or \
                   (verification_title and verification_title not in self.driver.title) or \
                   (not verification_url and not verification_title and 
                    (self.driver.current_url != current_url or current_title != self.driver.title)):
                    logger.info("Click verified successful - page changed")
                    return True
                else:
                    logger.warning("Click reported success but page didn't change")
                    return False
            return True
        except Exception as e:
            logger.error(f"Failed to click element: {e}")
            return False
    
    def fill_input_field(self, element: WebElement, value: str, clear_first: bool = True) -> bool:
        """Fill input field with value."""
        try:
            if clear_first:
                element.clear()
            element.send_keys(value)
            logger.info(f"Filled input field with value: {value[:10]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to fill input field: {e}")
            return False
    
    def submit_form(self, element: WebElement) -> bool:
        """Submit form by sending RETURN key."""
        try:
            element.send_keys(Keys.RETURN)
            logger.info("Form submitted with RETURN key")
            return True
        except Exception as e:
            logger.error(f"Failed to submit form: {e}")
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


class AuthenticationUtils:
    """Generic authentication utilities including OTP/TOTP handling."""
    
    def __init__(self, driver):
        self.driver = driver
        self.element_utils = ElementUtils(driver)
        self.browser_utils = BrowserUtils(driver)
    
    def handle_totp_verification(self, totp_secret: str, 
                                otp_selectors: List[Tuple[str, str]] = None,
                                submit_selectors: List[Tuple[str, str]] = None) -> bool:
        """Handle TOTP verification with generic selectors."""
        if otp_selectors is None:
            otp_selectors = [
                (By.ID, "idTxtBx_SAOTCC_OTC"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.CSS_SELECTOR, "input[name='otc']")
            ]
        
        if submit_selectors is None:
            submit_selectors = [
                (By.XPATH, "//input[@type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Verify')]")
            ]
        
        # Check if we're on a verification page
        verification_keywords = ['verification', 'code', 'authenticator', 'OTP', '2FA']
        verify_elements = self.element_utils.find_elements_by_text_pattern(verification_keywords)
        
        if not verify_elements:
            logger.info("No verification page detected")
            return True
        
        logger.info("Detected verification page, handling TOTP")
        self.browser_utils.save_screenshot("verification_page.png")
        
        # Generate TOTP code
        try:
            totp = pyotp.TOTP(totp_secret)
            auth_code = totp.now()
            logger.info(f"Generated TOTP code: {auth_code}")
        except Exception as e:
            logger.error(f"Failed to generate TOTP code: {e}")
            return False
        
        # Find and fill OTP input
        otp_input = self.element_utils.find_element_with_fallback(otp_selectors, timeout=10)
        if not otp_input:
            logger.error("OTP input field not found")
            self.browser_utils.save_screenshot("otp_page_not_found.png")
            return False
        
        if not self.element_utils.fill_input_field(otp_input, auth_code):
            return False
        
        # Find and click submit button
        submit_btn = self.element_utils.find_clickable_element(submit_selectors, timeout=5)
        if not submit_btn:
            logger.error("OTP submit button not found")
            return False
        
        if not self.element_utils.click_element(submit_btn):
            return False
        
        time.sleep(3)  # Wait for submission
        
        # Handle "Stay signed in" prompt
        self._handle_stay_signed_in_prompt()
        
        return True
    
    def _handle_stay_signed_in_prompt(self):
        """Handle 'Stay signed in' prompt that may appear after OTP."""
        yes_button_selectors = [
            (By.ID, "idSIButton9"),
            (By.XPATH, "//button[contains(text(), 'Yes')]"),
            (By.XPATH, "//input[@value='Yes']"),
            (By.XPATH, "//button[contains(@class, 'primary')]")
        ]
        
        for by_method, selector in yes_button_selectors:
            try:
                yes_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((by_method, selector))
                )
                logger.info(f"Found 'Stay signed in' prompt, clicking: {selector}")
                yes_button.click()
                time.sleep(2)
                break
            except TimeoutException:
                continue


class LoginFlowManager:
    """Main login flow manager that orchestrates the entire login process."""
    
    def __init__(self, driver, config: Dict[str, Any]):
        self.driver = driver
        self.config = config
        self.browser_utils = BrowserUtils(driver)
        self.element_utils = ElementUtils(driver)
        self.form_utils = FormUtils(driver)
        self.auth_utils = AuthenticationUtils(driver)
    
    def execute_login_flow(self) -> bool:
        """Execute the complete login flow."""
        try:
            # Step 1: Navigate to login URL
            if not self.browser_utils.navigate_to_url(self.config['login_url']):
                return False
            
            # Step 2: Check if already logged in
            if self._is_already_logged_in():
                logger.info("Already logged in, skipping login steps")
                return True
            
            # Step 3: Initiate login process
            if not self._initiate_login():
                return False
            
            # Step 4: Handle authentication window
            if not self._handle_auth_window():
                return False
            
            # Step 5: Fill credentials
            if not self._fill_credentials():
                return False
            
            # Step 6: Handle sign-in and verification
            if not self._handle_sign_in_and_verification():
                return False
            
            # Step 7: Verify successful login
            return self._verify_successful_login()
            
        except Exception as e:
            logger.error(f"Login flow failed: {e}")
            return False
    
    def _is_already_logged_in(self) -> bool:
        """Check if already logged in by URL pattern."""
        return "/login" not in self.driver.current_url
    
    def _initiate_login(self) -> bool:
        """Click login button to initiate the login process."""
        login_button_selectors = [
            (By.CLASS_NAME, "btn-login"),
            (By.CSS_SELECTOR, "button[class*='login']"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.XPATH, "//a[contains(text(), 'Login')]")
        ]
        
        login_button = self.element_utils.find_clickable_element(login_button_selectors, timeout=3)
        if not login_button:
            logger.warning("Login button not found")
            return False
        
        if not self.element_utils.click_element(login_button, verify_click=False):
            return False
        
        logger.info("Login button clicked")
        return True
    
    def _handle_auth_window(self) -> bool:
        """Handle authentication window (same window or popup)."""
        # Try new window
        original_handle = self.driver.current_window_handle
        if self.browser_utils.switch_to_new_window(original_handle, timeout=10):
            return True
        
        logger.warning("Could not detect authentication window")
        return False
    
    def _fill_credentials(self) -> bool:
        """Fill email and password fields."""
        # Fill email
        if not self.form_utils.fill_email_field(self.config['email']):
            logger.error("Failed to fill email field")
            return False
        
        # Fill password
        if not self.form_utils.fill_password_field(self.config['password']):
            logger.error("Failed to fill password field")
            return False
        
        return True
    
    def _handle_sign_in_and_verification(self) -> bool:
        """Handle sign-in button and any verification required."""
        # Try to click sign-in button
        sign_in_selectors = [
            (By.ID, "idSIButton9"),
            (By.XPATH, "//button[contains(text(), 'Sign in')]"),
            (By.XPATH, "//input[@type='submit']")
        ]
        # Handle TOTP if configured
        if 'totp_secret' in self.config:
            if not self.auth_utils.handle_totp_verification(self.config['totp_secret']):
                logger.error("TOTP verification failed")
                return False
        
        # Handle window switching back to main app
        if 'target_url' in self.config:
            if not self.browser_utils.switch_to_window_by_url_contains(self.config['target_url']):
                logger.warning("Could not switch back to main application window")
        
        return True
    
    def _verify_successful_login(self) -> bool:
        """Verify that login was successful."""
        if 'target_url' in self.config:
            return self.browser_utils.wait_for_url_contains(self.config['target_url'], timeout=15)
        return True


def create_login_config() -> Dict[str, Any]:
    """Create login configuration from environment variables."""
    return {
        'login_url': os.getenv("FARM_APP_LOGIN_URL"),
        'email': os.getenv("FARM_APP_EMAIL"),
        'password': os.getenv("FARM_APP_PASSWORD"),
        'totp_secret': os.getenv("FARM_APP_TOTP_SECRET"),
        'target_url': os.getenv("FARM_APP_LOGIN_URL")  # Use login URL as target for verification
    }


def main():
    """Main function to execute the login flow."""
    driver = get_driver()
    config = create_login_config()
    
    login_manager = LoginFlowManager(driver, config)
    success = login_manager.execute_login_flow()
    
    if success:
        logger.info("Login completed successfully")
    else:
        logger.error("Login failed")
    
    logger.info("Login script completed.")
    logger.info("-------------------------")


if __name__ == "__main__":
    main()