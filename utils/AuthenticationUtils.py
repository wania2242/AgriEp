from typing import List, Tuple
import pyotp
import time
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from utils.BrowserUtils import BrowserUtils
from utils.ElementUtils import ElementUtils
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
