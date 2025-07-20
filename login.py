from shared_driver import get_driver
from selenium.webdriver.common.by import By
import time
import os
from dotenv import load_dotenv
from typing import List, Tuple, Dict, Any
import logging
from utils.BrowserUtils import BrowserUtils
from utils.ElementUtils import ElementUtils
from utils.RetryMechanism import RetryMechanism
from utils.FormUtils import FormUtils
from utils.AuthenticationUtils import AuthenticationUtils
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
class LoginFlowManager:
    """Main login flow manager that orchestrates the entire login process with robust error handling."""
    
    def __init__(self, driver, config: Dict[str, Any]):
        self.driver = driver
        self.config = config
        self.browser_utils = BrowserUtils(driver)
        self.element_utils = ElementUtils(driver)
        self.form_utils = FormUtils(driver)
        self.auth_utils = AuthenticationUtils(driver)
        self.retry_mechanism = RetryMechanism(max_retries=3, base_delay=2.0, max_delay=15.0)
    
    def execute_login_flow(self) -> bool:
        """Execute the complete login flow with robust error handling."""
        try:
            # Step 1: Navigate to login URL with retry
            navigation_success = self.retry_mechanism.execute_with_retry(
                lambda: self.browser_utils.navigate_to_url(self.config['login_url']),
                "Navigation to login URL"
            )
            if not navigation_success:
                return False
            
            # Step 2: Check if already logged in
            if self._is_already_logged_in():
                logger.info("Already logged in, skipping login steps")
                return True
            
            # Step 3: Initiate login process with retry
            login_init_success = self.retry_mechanism.execute_with_retry(
                self._initiate_login,
                "Login initiation"
            )
            if not login_init_success:
                return False
            
            # Step 4: Handle authentication window with retry
            auth_window_success = self.retry_mechanism.execute_with_retry(
                self._handle_auth_window,
                "Authentication window handling"
            )
            if not auth_window_success:
                return False
            
            # Step 5: Fill credentials with retry
            credentials_success = self.retry_mechanism.execute_with_retry(
                self._fill_credentials,
                "Credentials filling"
            )
            if not credentials_success:
                return False
            
            # Step 6: Handle sign-in and verification with retry
            sign_in_success = self.retry_mechanism.execute_with_retry(
                self._handle_sign_in_and_verification,
                "Sign-in and verification"
            )
            if not sign_in_success:
                return False
            
            # Step 7: Verify successful login
            return self._verify_successful_login()
            
        except Exception as e:
            logger.error(f"Login flow failed: {e}")
            # Save debug information
            self.browser_utils.save_screenshot("login_failure.png")
            self.browser_utils.save_page_source("login_failure.html")
            return False
    
    def _is_already_logged_in(self) -> bool:
        """Check if already logged in by URL pattern."""
        return "/login" not in self.driver.current_url
    
    def _initiate_login(self) -> bool:
        """Click login button to initiate the login process with robust waiting."""
        # Wait for page to be fully loaded before looking for login button
        self.browser_utils.robust_wait.wait_for_page_load(timeout=10)
        
        login_button_selectors = [
            (By.CLASS_NAME, "btn-login"),
            (By.CSS_SELECTOR, "button[class*='login']"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.XPATH, "//a[contains(text(), 'Login')]")
        ]
        
        login_button = self.element_utils.find_clickable_element(login_button_selectors, timeout=15)
        if not login_button:
            logger.warning("Login button not found")
            return False
        
        # Click with verification that something happened
        if not self.element_utils.click_element(login_button, verify_click=True):
            return False
        
        logger.info("Login button clicked successfully")
        return True
    
    def _handle_auth_window(self) -> bool:
        """Handle authentication window (same window or popup) with robust waiting."""
        # Wait for page transition after login button click
        self.browser_utils.robust_wait.wait_for_page_transition(timeout=15)
        
        # Try same window first
        if self.browser_utils.wait_for_url_contains("login.microsoftonline.com", timeout=10):
            logger.info("MS login page loaded in same window")
            return True
        
        # Try new window
        original_handle = self.driver.current_window_handle
        if self.browser_utils.switch_to_new_window(original_handle, timeout=10):
            return True
        
        logger.warning("Could not detect authentication window")
        return False
    
    def _fill_credentials(self) -> bool:
        """Fill email and password fields with robust waiting."""
        # Wait for page to be stable before filling credentials
        self.browser_utils.robust_wait.wait_for_page_load(timeout=10)
        
        # Fill email with retry
        email_success = self.retry_mechanism.execute_with_retry(
            lambda: self.form_utils.fill_email_field(self.config['email']),
            "Email field filling"
        )
        if not email_success:
            logger.error("Failed to fill email field")
            return False
        
        # Wait for password field to appear
        time.sleep(2)
        
        # Fill password with retry
        password_success = self.retry_mechanism.execute_with_retry(
            lambda: self.form_utils.fill_password_field(self.config['password']),
            "Password field filling"
        )
        if not password_success:
            logger.error("Failed to fill password field")
            return False
        
        return True
    
    def _handle_sign_in_and_verification(self, click_sign_in_button: bool = False) -> bool:
        """Handle sign-in button and any verification required with robust waiting."""
        # Wait for page to be stable before looking for sign-in button
        self.browser_utils.robust_wait.wait_for_page_load(timeout=10)
        
        # Try to click sign-in button with retry
        if click_sign_in_button:
            sign_in_selectors = [
                (By.ID, "idSIButton9"),
                (By.XPATH, "//button[contains(text(), 'Sign in')]"),
                (By.XPATH, "//input[@type='submit']")
            ]
            
            sign_in_success = self.retry_mechanism.execute_with_retry(
                lambda: self._click_sign_in_button(sign_in_selectors),
                "Sign-in button clicking"
            )
            
            if not sign_in_success:
                logger.warning("Sign-in button not found or failed to click")
        
        # Handle TOTP if configured
        if 'totp_secret' in self.config:
            totp_success = self.retry_mechanism.execute_with_retry(
                lambda: self.auth_utils.handle_totp_verification(self.config['totp_secret']),
                "TOTP verification"
            )
            if not totp_success:
                logger.error("TOTP verification failed")
                return False
        
        # Handle window switching back to main app
        if 'target_url' in self.config:
            if not self.browser_utils.switch_to_window_by_url_contains(self.config['target_url']):
                logger.warning("Could not switch back to main application window")
        
        return True
    
    def _click_sign_in_button(self, selectors: List[Tuple[str, str]]) -> bool:
        """Helper method to click sign-in button."""
        sign_in_button = self.element_utils.find_clickable_element(selectors, timeout=15)
        if not sign_in_button:
            return False
        
        return self.element_utils.click_element(sign_in_button, verify_click=True)
    
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
        time.sleep(10)
    else:
        logger.error("Login failed")
    
    logger.info("Login script completed.")
    logger.info("-------------------------")


if __name__ == "__main__":
    main()