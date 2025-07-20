from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import gzip
from shared_driver import get_driver
from workorder_util import plot_selection_and_save
from selenium.common.exceptions import StaleElementReferenceException
from typing import Dict, Any, Optional, List, Tuple
import logging
from utils import (
    BrowserUtils,
    ElementUtils,
    RetryMechanism,
    DropdownUtils,
    NetworkUtils,
    ConfigUtils
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkOrderManager:
    """Main workorder flow manager that orchestrates the entire workorder process."""
    
    def __init__(self, driver):
        self.driver = driver
        self.browser_utils = BrowserUtils(driver)
        self.element_utils = ElementUtils(driver)
        self.dropdown_utils = DropdownUtils(driver)
        self.network_utils = NetworkUtils(driver)
        self.retry_mechanism = RetryMechanism(max_retries=3, base_delay=2.0, max_delay=15.0)
        
        # Load workorder configuration
        self.config = ConfigUtils.get_workorder_config()
    
    def execute_workorder_flow(self) -> Optional[int]:
        """Execute the complete workorder flow."""
        try:
            # Step 1: Navigate to workorders page
            if not self._navigate_to_workorders():
                return None
            
            # Step 2: Create new workorder
            if not self._create_new_workorder():
                return None
            
            # Step 3: Fill workorder form
            if not self._fill_workorder_form():
                return None
            
            # Step 4: Submit and save workorder
            workorder_id = self._submit_and_save_workorder()
            
            # Step 5: Open and edit workorder
            if workorder_id:
                self._open_and_edit_workorder(workorder_id)
            
            return workorder_id
            
        except Exception as e:
            logger.error(f"Workorder flow failed: {e}")
            self.browser_utils.save_screenshot("workorder_failure.png")
            self.browser_utils.save_page_source("workorder_failure.html")
            return None
    
    def _navigate_to_workorders(self) -> bool:
        """Navigate to the workorders page with optimization."""
        current_url = self.driver.current_url
        logger.info(f"Current URL before navigating: {current_url}")
        
        # Optimization: If already on the main application, use direct navigation
        if "agrierp-eh-pon-farms-qa-dfedaq0hegranhf.eastus-01.azurewebsites.net" in current_url:
            logger.info("Already on the main application - using fast navigation")
            self.driver.execute_script(
                "window.location.href = 'https://agrierp-eh-pon-farms-qa-dfedaq0hegranhf.eastus-01.azurewebsites.net/workorders';"
            )
        else:
            logger.info("Navigating to workorders page...")
            if not self.browser_utils.navigate_to_url(self.config['workorders_url']):
                return False
        
        # Wait for workorders page to load
        return self.retry_mechanism.execute_with_retry(
            self._wait_for_workorders_page,
            "Workorders page navigation"
        )
    
    def _wait_for_workorders_page(self) -> bool:
        """Wait for workorders page to be loaded."""
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'workorder') or contains(@class, 'work-order')] | //h1[contains(text(), 'Work')] | //table | //div[contains(@class, 'page-content')]")
                )
            )
            logger.info("Workorders page loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load workorders page: {e}")
            return False
    
    def _create_new_workorder(self) -> bool:
        """Click the 'Create New Work Orders' button."""
        create_button_selectors = [
            (By.XPATH, "//button[@class='btn btn-primary ml-2 h-100 btn-sm'][@title='Create New Work Orders']"),
            (By.XPATH, "//button[contains(text(), 'Create New Work Orders')]"),
            (By.XPATH, "//button[contains(@class, 'btn-primary')][contains(@class, 'btn-sm')]")
        ]
        
        return self.retry_mechanism.execute_with_retry(
            lambda: self._click_create_button(create_button_selectors),
            "Create new workorder button"
        )
    
    def _click_create_button(self, selectors: List[Tuple[str, str]]) -> bool:
        """Click the create workorder button."""
        create_button = self.element_utils.find_clickable_element(selectors, timeout=15)
        if not create_button:
            logger.error("Create New Work Orders button not found")
            return False
        
        if not self.element_utils.click_element(create_button, verify_click=False):
            return False
        
        # Wait for form to load
        return self._wait_for_workorder_form()
    
    def _wait_for_workorder_form(self) -> bool:
        """Wait for the workorder form to load."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'modal')] | //div[contains(@class, 'form')] | //h1[contains(text(), 'Create')] | //h1[contains(text(), 'New')] | //form")
                )
            )
            logger.info("Workorder form loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load workorder form: {e}")
            return False
    
    def _fill_workorder_form(self) -> bool:
        """Fill the workorder form with all required selections."""
        try:
            # Handle overlapping elements
            self.dropdown_utils.handle_overlapping_elements()
            
            # Step 1: Select farm
            if not self._select_farm():
                return False
            
            # Step 2: Select operation
            if not self._select_operation():
                return False
            
            # Step 3: Select supervisor
            if not self._select_supervisor():
                return False
            
            # Step 4: Select plots and fetch details
            if not self._select_plots_and_fetch():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill workorder form: {e}")
            return False
    
    def _select_farm(self) -> bool:
        """Select farm from dropdown."""
        logger.info("Starting farm selection...")
        
        farm_dropdown_selectors = [
            (By.XPATH, "//*[@id='select-farm']/div/button"),
            (By.XPATH, "//button[@type='button'][@data-toggle='dropdown'][contains(@class, 'btn') and contains(@class, 'dropdown-toggle')]")
        ]
        
        farm_option_selectors = [
            (By.XPATH, self.config['farm_option_xpath']),
            (By.XPATH, "//a[contains(@class, 'dropdown-item') and contains(text(), 'Farm')]")
        ]
        
        return self._select_from_dropdown("farm", farm_dropdown_selectors, farm_option_selectors)
    
    def _select_operation(self) -> bool:
        """Select operation from dropdown."""
        logger.info("Starting operation selection...")
        
        operation_dropdown_selectors = [
            (By.XPATH, "//*[@id='select-operation']/div/button")
        ]
        
        operation_option_selectors = [
            (By.XPATH, self.config['operation_option_xpath'])
        ]
        
        return self._select_from_dropdown("operation", operation_dropdown_selectors, operation_option_selectors)
    
    def _select_supervisor(self) -> bool:
        """Select supervisor from dropdown."""
        logger.info("Starting supervisor selection...")
        
        supervisor_dropdown_selectors = [
            (By.XPATH, "//*[@id='select-supervisor']/div/button")
        ]
        
        supervisor_option_selectors = [
            (By.XPATH, self.config['supervisor_option_xpath'])
        ]
        
        return self._select_from_dropdown("supervisor", supervisor_dropdown_selectors, supervisor_option_selectors)
    
    def _select_from_dropdown(self, dropdown_name: str, dropdown_selectors: List[Tuple[str, str]], 
                             option_selectors: List[Tuple[str, str]]) -> bool:
        """Generic method to select from dropdown."""
        # Open dropdown
        if not self.dropdown_utils.open_dropdown(dropdown_selectors, timeout=10):
            logger.error(f"Failed to open {dropdown_name} dropdown")
            return False
        
        # Select option
        if not self.dropdown_utils.select_dropdown_option(option_selectors, timeout=10):
            logger.error(f"Failed to select {dropdown_name} option")
            return False
        
        logger.info(f"{dropdown_name.capitalize()} selection completed")
        return True
    
    def _select_plots_and_fetch(self) -> bool:
        """Select plots and fetch details."""
        try:
            # Select plots using existing utility
            plot_selection_and_save(self.driver)
            logger.info("Plot selection completed")
            
            # Click Fetch Plot(s) Details button
            fetch_button_selectors = [
                (By.XPATH, "//*[@id='blocks']/app-work-order-activity-table/div[1]/div[1]/h3/span"),
                (By.CSS_SELECTOR, "span.ml-1.btn-link.btn-fetch-blocks"),
                (By.XPATH, "//span[contains(@class, 'btn-fetch-blocks')]"),
                (By.XPATH, "//span[.//i[contains(@class, 'fa-refresh')] and contains(text(), 'Fetch Plot(s) Details')]")
            ]
            
            fetch_button = self.element_utils.find_clickable_element(fetch_button_selectors, timeout=10)
            if not fetch_button:
                logger.error("Fetch Plot(s) Details button not found")
                return False
            
            if not self.element_utils.click_element(fetch_button, verify_click=False):
                return False
            
            logger.info("Fetch Plot(s) Details button clicked")
            return True
            
        except Exception as e:
            logger.error(f"Failed to select plots and fetch details: {e}")
            return False
    
    def _submit_and_save_workorder(self) -> Optional[int]:
        """Submit and save the workorder, returning the workorder ID."""
        try:
            # Click submit button
            submit_button_xpath = "/html/body/app-root/app-default-layout/div/app-aside/div/app-f3-aside-panel/div/app-planned-operations/div/div[1]/div/div/button"
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, submit_button_xpath))
            )
            submit_button.click()
            logger.info("Submit button clicked")
            
            # Click save button
            save_button_xpath = "//*[@id=\"mat-dialog-0\"]/app-work-order-action-dialog/div/div[2]/button[2]"
            save_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, save_button_xpath))
            )
            save_button.click()
            logger.info("Save button clicked")
            
            # Wait for save operation
            time.sleep(5)
            
            # Extract workorder ID from network response
            workorder_id = self.network_utils.extract_workorder_id_from_requests(
                self.config['api_url']
            )
            
            return workorder_id
            
        except Exception as e:
            logger.error(f"Failed to submit and save workorder: {e}")
            return None
    
    def _open_and_edit_workorder(self, workorder_id: int):
        """Open and edit the created workorder."""
        try:
            # Navigate to workorder details
            workorder_url = f"https://agrierp-eh-pon-farms-qa-dfedaqg0hegranhf.eastus-01.azurewebsites.net/workorders/{workorder_id}"
            logger.info(f"Navigating to workorder URL: {workorder_url}")
            self.driver.get(workorder_url)
            time.sleep(3)
            
            # Click recall button
            if not self._click_recall_button():
                return
            
            # Click edit button
            if not self._click_edit_button():
                return
            
            # Delete material from first row
            self._delete_material_from_first_row()
            
        except Exception as e:
            logger.error(f"Failed to open and edit workorder: {e}")
    
    def _click_recall_button(self) -> bool:
        """Click the recall button."""
        try:
            recall_button_xpath = "//*[@id=\"main-container\"]/app-work-order-details/div[1]/div[2]/div[2]/div/button[4]"
            recall_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, recall_button_xpath))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", recall_button)
            time.sleep(1)
            recall_button.click()
            logger.info("Recall button clicked")
            return True
        except Exception as e:
            logger.error(f"Failed to click recall button: {e}")
            return False
    
    def _click_edit_button(self) -> bool:
        """Click the edit button."""
        try:
            # Wait for overlay to disappear
            self.dropdown_utils.wait_for_overlay_disappear()
            
            edit_button_xpath = "//button[@title='Edit Work Order']"
            edit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, edit_button_xpath))
            )
            
            for attempt in range(3):
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", edit_button)
                    time.sleep(0.5)
                    edit_button.click()
                    logger.info("Edit button clicked")
                    return True
                except Exception as e:
                    logger.warning(f"Edit button click attempt {attempt+1} failed: {e}")
                    time.sleep(1)
            
            logger.error("Could not click edit button after multiple attempts")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click edit button: {e}")
            return False
    
    def _delete_material_from_first_row(self):
        """Delete material from the first row of the materials table."""
        try:
            # Scroll to materials section
            materials_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "materials"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", materials_div)
            time.sleep(1)
            logger.info("Scrolled to materials section")
            
            # Click delete button in first row
            delete_button_xpath = "//div[@id='materials']//table//tr[1]//span[@title='Remove material']/i[contains(@class, 'icon-remove-bin')]"
            
            for attempt in range(3):
                try:
                    delete_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, delete_button_xpath))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", delete_button)
                    time.sleep(1)
                    delete_button.click()
                    logger.info("Delete button clicked")
                    
                    # Handle confirmation alert
                    if self._handle_delete_confirmation():
                        # Submit changes
                        if self._submit_changes():
                            # Update workorder
                            self._update_workorder()
                    
                    break
                    
                except StaleElementReferenceException:
                    logger.warning(f"StaleElementReferenceException on attempt {attempt+1}, retrying...")
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Could not click delete button: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Failed to delete material from first row: {e}")
    
    def _handle_delete_confirmation(self) -> bool:
        """Handle the delete confirmation alert."""
        try:
            yes_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-success') and text()='Yes']"))
            )
            yes_button.click()
            logger.info("Clicked 'Yes' on delete confirmation")
            return True
        except Exception as e:
            logger.error(f"Failed to handle delete confirmation: {e}")
            return False
    
    def _submit_changes(self) -> bool:
        """Submit changes after deleting material."""
        try:
            submit_button_xpath = "/html/body/app-root/app-default-layout/div/app-aside/div/app-f3-aside-panel/div/app-planned-operations/div/div[1]/div/div/button"
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, submit_button_xpath))
            )
            submit_button.click()
            logger.info("Submit button clicked after deleting material")
            return True
        except Exception as e:
            logger.error(f"Failed to submit changes: {e}")
            return False
    
    def _update_workorder(self) -> bool:
        """Click the update button on the alert."""
        try:
            update_button_xpath = "/html/body/div[3]/div[2]/div/mat-dialog-container/app-work-order-action-dialog/div/div[2]/button[2]"
            update_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, update_button_xpath))
            )
            update_button.click()
            logger.info("Update button clicked on alert")
            return True
        except Exception as e:
            logger.error(f"Failed to update workorder: {e}")
            return False


def main():
    """Main function to execute the workorder flow."""
    logger.info("Starting workorder operations...")
    
    driver = get_driver()
    workorder_manager = WorkOrderManager(driver)
    
    workorder_id = workorder_manager.execute_workorder_flow()
    
    if workorder_id:
        logger.info(f"Workorder operations completed successfully. WorkOrder ID: {workorder_id}")
    else:
        logger.error("Workorder operations failed")
    
    logger.info("Workorder script completed.")


if __name__ == "__main__":
    main()
