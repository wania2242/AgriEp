"""
Dropdown interaction utilities for web automation.

This module provides utilities for:
- Opening dropdowns
- Selecting dropdown options
- Handling dropdown menus
- Verifying dropdown selections
"""

import time
import logging
from typing import List, Tuple, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from .ElementUtils import ElementUtils
from .WaitUtils import RobustWaitUtils

logger = logging.getLogger(__name__)

class DropdownUtils:
    """Utilities for handling dropdown interactions."""
    
    def __init__(self, driver):
        self.driver = driver
        self.element_utils = ElementUtils(driver)
        self.robust_wait = RobustWaitUtils(driver)
    
    def open_dropdown(self, dropdown_selectors: List[Tuple[str, str]], 
                     timeout: int = 10) -> bool:
        """Open a dropdown using multiple selector strategies."""
        for by_method, selector in dropdown_selectors:
            try:
                # Wait for page to be stable
                self.robust_wait.wait_for_page_load(min(timeout, 5))
                
                # Find and click the dropdown button
                dropdown_button = self.element_utils.find_clickable_element(
                    [(by_method, selector)], timeout=timeout
                )
                
                if not dropdown_button:
                    continue
                
                # Scroll into view
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                    dropdown_button
                )
                time.sleep(1)
                
                # Try multiple click methods
                click_success = False
                
                # Method 1: JavaScript click
                try:
                    self.driver.execute_script("""
                        arguments[0].style.opacity = '1';
                        arguments[0].style.visibility = 'visible';
                        arguments[0].style.pointerEvents = 'auto';
                        arguments[0].click();
                    """, dropdown_button)
                    click_success = True
                    logger.info("Dropdown opened using JavaScript")
                except Exception as js_error:
                    logger.warning(f"JavaScript click failed: {js_error}")
                
                # Method 2: Native click
                if not click_success:
                    try:
                        dropdown_button.click()
                        click_success = True
                        logger.info("Dropdown opened using native click")
                    except Exception as native_error:
                        logger.warning(f"Native click failed: {native_error}")
                
                # Method 3: ActionChains
                if not click_success:
                    try:
                        actions = ActionChains(self.driver)
                        actions.move_to_element(dropdown_button).click().perform()
                        click_success = True
                        logger.info("Dropdown opened using ActionChains")
                    except Exception as action_error:
                        logger.warning(f"ActionChains click failed: {action_error}")
                
                if click_success:
                    # Wait for dropdown menu to be visible
                    if self._wait_for_dropdown_menu(timeout=5):
                        logger.info(f"Dropdown opened successfully with selector: {by_method}={selector}")
                        return True
                
            except Exception as e:
                logger.warning(f"Failed to open dropdown with selector {by_method}={selector}: {e}")
                continue
        
        logger.error("Failed to open dropdown with any selector")
        return False
    
    def select_dropdown_option(self, option_selectors: List[Tuple[str, str]], 
                              timeout: int = 10) -> bool:
        """Select an option from an open dropdown."""
        for by_method, selector in option_selectors:
            try:
                # Wait for option to be clickable
                option = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by_method, selector))
                )
                
                # Scroll option into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
                time.sleep(0.5)
                
                # Try multiple click methods
                click_success = False
                
                # Method 1: Native click
                try:
                    option.click()
                    click_success = True
                    logger.info("Option selected using native click")
                except Exception as native_error:
                    logger.warning(f"Native click failed: {native_error}")
                
                # Method 2: ActionChains
                if not click_success:
                    try:
                        actions = ActionChains(self.driver)
                        actions.move_to_element(option).click().perform()
                        click_success = True
                        logger.info("Option selected using ActionChains")
                    except Exception as action_error:
                        logger.warning(f"ActionChains click failed: {action_error}")
                
                # Method 3: JavaScript click
                if not click_success:
                    try:
                        self.driver.execute_script(
                            "arguments[0].click(); arguments[0].dispatchEvent(new Event('click'));",
                            option
                        )
                        click_success = True
                        logger.info("Option selected using JavaScript")
                    except Exception as js_error:
                        logger.warning(f"JavaScript click failed: {js_error}")
                
                if click_success:
                    # Verify dropdown is closed
                    if self._wait_for_dropdown_closed(timeout=5):
                        logger.info(f"Option selected successfully with selector: {by_method}={selector}")
                        return True
                
            except Exception as e:
                logger.warning(f"Failed to select option with selector {by_method}={selector}: {e}")
                continue
        
        logger.error("Failed to select dropdown option with any selector")
        return False
    
    def _wait_for_dropdown_menu(self, timeout: int = 5) -> bool:
        """Wait for dropdown menu to be visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'dropdown-menu') and contains(@class, 'show')]")
                )
            )
            return True
        except TimeoutException:
            logger.warning("Dropdown menu not visible within timeout")
            return False
    
    def _wait_for_dropdown_closed(self, timeout: int = 5) -> bool:
        """Wait for dropdown menu to be closed."""
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'dropdown-menu') and contains(@class, 'show')]")
                )
            )
            return True
        except TimeoutException:
            logger.warning("Dropdown menu still visible after selection")
            return False
    
    def handle_overlapping_elements(self):
        """Handle overlapping elements that might interfere with dropdown interactions."""
        try:
            # Force disable and hide any overlapping Save As button
            self.driver.execute_script("""
                var saveButton = document.querySelector('button[title="Save As"]');
                if (saveButton) {
                    saveButton.style.pointerEvents = 'none';
                    saveButton.style.display = 'none';
                    saveButton.disabled = true;
                }
            """)
            
            # Wait a moment for the DOM to update
            time.sleep(1)
            logger.info("Handled overlapping elements")
        except Exception as e:
            logger.warning(f"Error handling overlapping elements: {e}")
    
    def wait_for_overlay_disappear(self, overlay_id: str = "f3-overlay-loader", 
                                  timeout: int = 15) -> bool:
        """Wait for overlay to disappear before interacting with elements."""
        try:
            logger.info(f"Waiting for overlay '{overlay_id}' to disappear...")
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.ID, overlay_id))
            )
            # Extra: Wait for overlay to be removed from DOM
            WebDriverWait(self.driver, 5).until_not(
                EC.presence_of_element_located((By.ID, overlay_id))
            )
            logger.info("Overlay has disappeared")
            time.sleep(1)  # Small buffer
            return True
        except TimeoutException:
            logger.warning(f"Overlay did not disappear in time")
            return False 