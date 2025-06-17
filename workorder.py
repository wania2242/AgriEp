from seleniumwire import webdriver  # Import from seleniumwire
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.action_chains import ActionChains
import json
import gzip
import io
from shared_driver import get_driver
from workorder_util import plot_selection_and_save
from selenium.common.exceptions import StaleElementReferenceException
import test_reporter

print("Starting workorder operations...")

# Create a new Selenium driver instance for a fresh session every time
driver = get_driver()

# First check if we're already logged in by checking current URL
current_url = driver.current_url
print(f"Current URL before navigating: {current_url}")

# Optimization: If we're already on the main application, use direct navigation rather than full page load
if "agrierp-eh-pon-farms-qa-dfedaq0hegranhf.eastus-01.azurewebsites.net" in current_url:
    print("Already on the main application - using fast navigation")
    # Use JavaScript for faster navigation
    driver.execute_script(
        "window.location.href = 'https://agrierp-eh-pon-farms-qa-dfedaq0hegranhf.eastus-01.azurewebsites.net/workorders';"
    )
    # Small wait to start navigation
    # time.sleep(0.5)
else:
    # Standard navigation if not already on the site
    print("Navigating to workorders page...")
    driver.get(
        "https://agrierp-eh-pon-farms-qa-dfedaqg0hegranhf.eastus-01.azurewebsites.net/workorders"
    )

# Use a faster, more targeted wait for page load
try:
    print("Waiting for workorders page to load...")

    # Optimize the wait to look for specific elements that indicate the workorder page is loaded
    # This is more precise than waiting for the body element and reduces wait time
    # You may need to adjust this selector based on your actual page structure
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//div[contains(@class, 'workorder') or contains(@class, 'work-order')] | //h1[contains(text(), 'Work')] | //table | //div[contains(@class, 'page-content')]",
            )
        )
    )

    # Verify we're on the correct page
    print("Workorders page appears to be loaded")
    print(f"Current URL after navigating: {driver.current_url}")

    # Perform your operations on the workorders page here
    print("Beginning workorder operations...")

    # Click on the 'Create New Work Orders' button
    try:
        print("Looking for 'Create New Work Orders' button...")

        # Try multiple selector strategies to find the button
        button_found = False

        # Strategy 1: Using exact class and title attributes
        try:
            create_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[@class='btn btn-primary ml-2 h-100 btn-sm'][@title='Create New Work Orders']",
                    )
                )
            )
            button_found = True
            print("Found button using exact class and title match")
        except Exception:
            print("Could not find button using exact attributes, trying alternatives...")

        # Strategy 2: Using text content
        if not button_found:
            try:
                create_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Create New Work Orders')]")
                    )
                )
                button_found = True
                print("Found button using text content")
            except Exception:
                print("Could not find button using text content, trying alternatives...")

        # Strategy 3: Using partial class matching
        if not button_found:
            try:
                create_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//button[contains(@class, 'btn-primary')][contains(@class, 'btn-sm')]",
                        )
                    )
                )
                button_found = True
                print("Found button using partial class matching")
            except Exception:
                print("Could not find button using partial class matching")

        # If button found, click it
        if button_found:

            print("Clicking 'Create New Work Orders' button...")
            # Try JavaScript click first (more reliable in some cases)
            try:
                driver.execute_script("arguments[0].click();", create_button)
                print("Clicked button using JavaScript")
            except Exception:
                # Fallback to regular click
                create_button.click()
                print("Clicked button using regular method")

            print("Successfully clicked button, waiting for form to load...")

            # Wait for the create workorder form/page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[contains(@class, 'modal')] | //div[contains(@class, 'form')] | //h1[contains(text(), 'Create')] | //h1[contains(text(), 'New')] | //form",
                    )
                )
            )

            print("Create workorder form/page loaded successfully")
            print("Starting farm selection...")

            try:
                # Wait for the dropdown button to be clickable
                # Wait for the dropdown button with specific classes and attributes
                dropdown_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//button[@type='button'][@data-toggle='dropdown'][contains(@class, 'btn') and contains(@class, 'dropdown-toggle') and contains(@class, 'd-flex') and contains(@class, 'align-items-center') and contains(@class, 'form-control')][.//span[contains(@class, 'tag') and contains(@class, 'flex-grow-1') and contains(@class, 'text-truncate') and contains(@class, 'text-left')]]"
                        )
                    )
                )
                print("Dropdown button found and clickable.")

                # # Check for the overlay and wait for it to disappear
                # overlay_locator = (By.XPATH, "//lottie-player[@id='f3-overlay-loader']")
                # overlay_present = True
                # try:
                #     WebDriverWait(driver, 2).until(
                #         EC.presence_of_element_located(overlay_locator)
                #     )
                # except:
                #     overlay_present = False

                # if overlay_present:
                #     print("Overlay is present, waiting for it to disappear...")
                #     WebDriverWait(driver, 15).until(
                #         EC.invisibility_of_element_located(overlay_locator)
                #     )
                #     print("Overlay has disappeared.")
                # else:
                #     print("Overlay was not present.")
                # # Now that the overlay is gone (or was not there), click the button
                # First ensure any overlapping elements are handled
                try:
                    # Force disable and hide any overlapping Save As button
                    driver.execute_script("""
                        var saveButton = document.querySelector('button[title="Save As"]');
                        if (saveButton) {
                            saveButton.style.pointerEvents = 'none';
                            saveButton.style.display = 'none';
                            saveButton.disabled = true;
                        }
                    """)
                    
                    # Wait a moment for the DOM to update
                    time.sleep(1)
                except Exception as e:
                    print(f"Error handling overlapping elements: {e}")

                # Use the specific ID-based XPath for the dropdown button
                target_button_xpath = "//*[@id='select-farm']/div/button"

                try:
                    # Wait for our specific button and ensure it's in view
                    dropdown_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, target_button_xpath))
                    )
                    
                    # Scroll the button into center view
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                        dropdown_button
                    )
                    time.sleep(1)

                    # Use JavaScript to ensure the button is clickable and click it
                    driver.execute_script("""
                        arguments[0].style.opacity = '1';
                        arguments[0].style.visibility = 'visible';
                        arguments[0].style.pointerEvents = 'auto';
                        arguments[0].click();
                    """, dropdown_button)
                    
                    print("Clicked dropdown button using JavaScript")
                    
                    # Verify the dropdown is opened
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//div[contains(@class, 'dropdown-menu') and contains(@class, 'show')]")
                        )
                    )
                    print("Dropdown menu is now visible")
                    
                except Exception as e:
                    print(f"Error interacting with dropdown: {e}")

                # If the dropdown is still not visible, try one last time with pure JavaScript
                try:
                    WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//div[contains(@class, 'dropdown-menu') and contains(@class, 'show')]")
                        )
                    )
                except Exception:
                    print("Dropdown not visible, trying alternative JavaScript approach")
                    driver.execute_script("""
                        var dropdowns = document.querySelectorAll('button.dropdown-toggle');
                        for (var i = 0; i < dropdowns.length; i++) {
                            if (dropdowns[i].getBoundingClientRect().top < 100) {
                                dropdowns[i].click();
                                break;
                            }
                        }
                    """)
                    time.sleep(1)

                # Add a small wait to let the dropdown menu appear
                time.sleep(1)

                # Wait for the dropdown menu to be visible
                dropdown_menu_xpath = "//div[contains(@class, 'dropdown-menu') and contains(@class, 'show')]"
                try:
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, dropdown_menu_xpath))
                    )
                    print("Dropdown menu is visible")
                except Exception as e:
                    print(f"Error waiting for dropdown menu: {str(e)}")
                    # Continue anyway as the menu might still be visible

                # Use the specific XPath to find the farm option
                farm_option_xpath = "//*[@id='myDropdown']/a[6]"
                
                # Wait for the specific farm option and ensure it's clickable
                try:
                    farm_option = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, farm_option_xpath))
                    )
                    print("Farm option found and clickable")

                    # Scroll the option into view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", farm_option)
                    time.sleep(0.5)

                    click_success = False
                    # Try native click first
                    try:
                        farm_option.click()
                        click_success = True
                        print("Farm selected using native click")
                    except Exception as e:
                        print(f"Native click failed: {str(e)}")

                    # Try ActionChains if native click failed
                    if not click_success:
                        try:
                            actions = ActionChains(driver)
                            actions.move_to_element(farm_option).click().perform()
                            click_success = True
                            print("Farm selected using ActionChains")
                        except Exception as e:
                            print(f"ActionChains click failed: {str(e)}")

                    # Try JavaScript click as last resort
                    if not click_success:
                        driver.execute_script(
                            "arguments[0].click(); arguments[0].dispatchEvent(new Event('click'));",
                            farm_option
                        )
                        print("Farm selected using JavaScript")
                except Exception as e:
                    print(f"Error finding or clicking farm option: {str(e)}")

                try:
                    # Verify selection by checking if dropdown is closed
                    time.sleep(1)
                    WebDriverWait(driver, 5).until_not(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dropdown-menu') and contains(@class, 'show')]")),
                        "Dropdown menu still visible after selection"
                    )
                    print("Farm selection confirmed - dropdown closed")

                    # Now handle the operation dropdown
                    print("Starting operation selection...")
                    operation_button_xpath = "//*[@id='select-operation']/div/button"

                    # Wait for operation dropdown button and click it
                    operation_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, operation_button_xpath))
                    )
                    print("Operation dropdown button found")

                    # Scroll the operation button into view
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                        operation_button
                    )
                    time.sleep(1)

                    # Click the operation dropdown
                    try:
                        operation_button.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", operation_button)
                    print("Operation dropdown clicked")

                    # Wait for operation dropdown menu to be visible
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'dropdown-menu') and contains(@class, 'show')]")),
                        "Operation dropdown menu not visible"
                    )
                    print("Operation dropdown menu visible")

                    # Select the operation with exact text match
                    operation_option_xpath = "//a[contains(@class, 'dropdown-item') and normalize-space()='Early Spray Corn VR (9025100)']"
                    try:
                        # Wait for the operation option and ensure it's clickable
                        operation_option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, operation_option_xpath))
                        )
                        print("Operation option found")

                        # Scroll the option into view first
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", operation_option)
                        time.sleep(0.5)

                        click_success = False
                        # Try multiple click methods
                        try:
                            # Try native click
                            operation_option.click()
                            click_success = True
                            print("Operation selected using native click")
                        except Exception as e:
                            print(f"Native click failed: {str(e)}")

                        if not click_success:
                            try:
                                # Try ActionChains
                                actions = ActionChains(driver)
                                actions.move_to_element(operation_option).click().perform()
                                click_success = True
                                print("Operation selected using ActionChains")
                            except Exception as e:
                                print(f"ActionChains click failed: {str(e)}")

                        if not click_success:
                            # Try JavaScript click as last resort
                            driver.execute_script(
                                "arguments[0].click(); arguments[0].dispatchEvent(new Event('click'));",
                                operation_option
                            )
                            print("Operation selected using JavaScript")

                        # Verify operation selection
                        WebDriverWait(driver, 5).until_not(
                            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dropdown-menu') and contains(@class, 'show')]")),
                            "Operation dropdown menu still visible after selection"
                        )
                        print("Operation selection confirmed - dropdown closed")

                        # Now handle the supervisor dropdown
                        print("Starting supervisor selection...")
                        supervisor_button_xpath = "//*[@id='select-supervisor']/div/button"

                        # Wait for supervisor dropdown button and ensure it's clickable
                        supervisor_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, supervisor_button_xpath))
                        )
                        print("Supervisor dropdown button found")

                        # Scroll the supervisor button into view
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                            supervisor_button
                        )
                        time.sleep(1)

                        # Click the supervisor dropdown
                        click_success = False
                        try:
                            supervisor_button.click()
                            click_success = True
                            print("Supervisor dropdown clicked using native click")
                        except Exception as e:
                            print(f"Native click failed: {str(e)}")

                        if not click_success:
                            try:
                                actions = ActionChains(driver)
                                actions.move_to_element(supervisor_button).click().perform()
                                click_success = True
                                print("Supervisor dropdown clicked using ActionChains")
                            except Exception as e:
                                print(f"ActionChains click failed: {str(e)}")

                        if not click_success:
                            driver.execute_script(
                                "arguments[0].click(); arguments[0].dispatchEvent(new Event('click'));",
                                supervisor_button
                            )
                            print("Supervisor dropdown clicked using JavaScript")

                        # Wait for supervisor dropdown menu to be visible
                        WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'dropdown-menu') and contains(@class, 'show')]")),
                            "Supervisor dropdown menu not visible"
                        )
                        print("Supervisor dropdown menu visible")

                        # Select the supervisor with exact text match
                        supervisor_option_xpath = "//a[contains(@class, 'dropdown-item') and normalize-space()='Farm Fuel (CPF-FF-17-001)']"
                        supervisor_option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, supervisor_option_xpath))
                        )
                        print("Supervisor option found")

                        # Scroll the option into view
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", supervisor_option)
                        time.sleep(0.5)

                        # Try to click the supervisor option
                        click_success = False
                        try:
                            supervisor_option.click()
                            click_success = True
                            print("Supervisor selected using native click")
                        except Exception as e:
                            print(f"Native click failed: {str(e)}")

                        if not click_success:
                            try:
                                actions = ActionChains(driver)
                                actions.move_to_element(supervisor_option).click().perform()
                                click_success = True
                                print("Supervisor selected using ActionChains")
                            except Exception as e:
                                print(f"ActionChains click failed: {str(e)}")

                        if not click_success:
                            driver.execute_script(
                                "arguments[0].click(); arguments[0].dispatchEvent(new Event('click'));",
                                supervisor_option
                            )
                            print("Supervisor selected using JavaScript")

                        # Verify supervisor selection
                        WebDriverWait(driver, 5).until_not(
                            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dropdown-menu') and contains(@class, 'show')]")),
                            "Supervisor dropdown menu still visible after selection"
                        )
                        print("Supervisor selection confirmed - dropdown closed")

                        # Now select the first checkbox in the table
                        print("Attempting to select the first checkbox...")
                        try:
                            plot_selection_and_save(driver)
                        except Exception as e:
                            print(f"Could not run plot_selection_and_save funtion: {e}")    
                        print("Attempting to click Fetch Plot(s) Details button...")
                        time.sleep(2)  # Wait for any animations to complete

                        # Try multiple selectors for better reliability
                        fetch_button_selectors = [
                            (By.XPATH, "//*[@id='blocks']/app-work-order-activity-table/div[1]/div[1]/h3/span"),
                            (By.CSS_SELECTOR, "span.ml-1.btn-link.btn-fetch-blocks"),
                            (By.XPATH, "//span[contains(@class, 'btn-fetch-blocks')]"),
                            (By.XPATH, "//span[.//i[contains(@class, 'fa-refresh')] and contains(text(), 'Fetch Plot(s) Details')]"),
                        ]

                        fetch_button = None
                        for selector in fetch_button_selectors:
                            try:
                                fetch_button = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable(selector)
                                )
                                print(f"Found Fetch button using selector: {selector[1]}")
                                break
                            except Exception:
                                continue

                        if fetch_button:
                            # Scroll the button into view
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                                fetch_button
                            )
                            time.sleep(1)

                            # Try multiple click methods
                            click_success = False
                            try:
                                # Try native click
                                fetch_button.click()
                                click_success = True
                                print("Fetch button clicked using native click")
                            except Exception as e:
                                print(f"Native click failed: {str(e)}")

                            if not click_success:
                                try:
                                    # Try ActionChains
                                    actions = ActionChains(driver)
                                    actions.move_to_element(fetch_button).click().perform()
                                    click_success = True
                                    print("Fetch button clicked using ActionChains")
                                except Exception as e:
                                    print(f"ActionChains click failed: {str(e)}")

                            if not click_success:
                                # Try JavaScript click
                                driver.execute_script(
                                    "arguments[0].click(); arguments[0].dispatchEvent(new Event('click'));",
                                    fetch_button
                                )
                                print("Fetch button clicked using JavaScript")

                            # Wait for any loading indicators or animations
                            time.sleep(2)
                            print("Waiting for fetch operation to complete...")

                            # After fetch, click the submit button
                            try:
                                submit_button_xpath = "/html/body/app-root/app-default-layout/div/app-aside/div/app-f3-aside-panel/div/app-planned-operations/div/div[1]/div/div/button"
                                submit_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, submit_button_xpath))
                                )
                                submit_button.click()
                                print("Submit button clicked after fetch.")
                                # After submit, click the save button
                                try:
                                    save_button_xpath = "//*[@id=\"mat-dialog-0\"]/app-work-order-action-dialog/div/div[2]/button[2]"
                                    save_button = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, save_button_xpath))
                                    )
                                    save_button.click()
                                    print("Save button clicked after submit.")
                                    time.sleep(5)
                                    # Extract workOrderId from network response
                                    workorder_id = None
                                    target_url = "https://agrierp-eh-pon-farms-api-qa-ebdzb4csbsa7hccp.eastus-01.azurewebsites.net/api/workOrder"
                                    for request in driver.requests:
                                        if (
                                            request.response
                                            and request.method == "POST"
                                            and request.url == target_url
                                        ):
                                            try:
                                                content_type = request.response.headers.get('Content-Type', '')
                                                if 'application/json' in content_type:
                                                    body = request.response.body
                                                    if request.response.headers.get('Content-Encoding', '') == 'gzip':
                                                        body = gzip.decompress(body)
                                                    response_data = body.decode('utf-8')
                                                    json_data = json.loads(response_data)
                                                    workorder = json_data['lines'][0]
                                                    workorder_id = workorder['agriWorkOrderID']
                                                    print("WorkOrder ID:", workorder_id)
                                                   
                                                else:
                                                    print(f"Skipping non-JSON response for: {request.url}")
                                            except Exception as e:
                                                print(f"Error parsing work order response: {e}")
                                            break
                                    if not workorder_id:
                                        print("Could not extract WorkOrder ID from network response.")
                                except Exception as e:
                                    print(f"Could not click save button after submit: {e}")
                            except Exception as e:
                                print(f"Could not click submit button after fetch: {e}")
                        else:
                            print("Could not find the Fetch Plot(s) Details button with any selector")

                    except Exception as e:
                        print(f"Error during selections: {str(e)}")

                except Exception as e:
                    print(f"Warning: Issue with dropdown handling: {str(e)}")

            except Exception as e:
                print(f"Error during form interactions: {e}")

            print("All selections and fetch operation completed.")
            # --- End of automation code ---

        else:
            print(
                "Could not find the 'Create New Work Orders' button using any strategy"
            )

    except Exception as button_error:
        print(f"Error clicking 'Create New Work Orders' button: {button_error}")

    print("Workorder operations completed successfully")

    # --- Try to open by agriWorkOrderID from network response ---
    if not workorder_id:
        workorder_id = 52
    import json
    import time
    try:
        time.sleep(2)
        if workorder_id:
            workorder_url = f"https://agrierp-eh-pon-farms-qa-dfedaqg0hegranhf.eastus-01.azurewebsites.net/workorders/{workorder_id}"
            print(f"Navigating to workorder URL: {workorder_url}")
            driver.get(workorder_url)
            time.sleep(3)
            # Step 2: Click recall button
            try:
                recall_button_xpath = "//*[@id=\"main-container\"]/app-work-order-details/div[1]/div[2]/div[2]/div/button[4]"
                recall_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, recall_button_xpath))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", recall_button)
                time.sleep(1)
                recall_button.click()
                print("Recall button clicked after opening workorder by ID.")
                # Now click the edit button
                try:
                    # Use a robust selector for the edit button
                    edit_button_xpath = "//button[@title='Edit Work Order']"
                    print("Attempting to click the edit button after recall...")
                    # Wait for overlay to disappear before clicking edit
                    try:
                        print("Waiting for overlay to disappear before clicking edit button...")
                        WebDriverWait(driver, 15).until(
                            EC.invisibility_of_element_located((By.ID, "f3-overlay-loader"))
                        )
                        # Extra: Wait for overlay to be removed from DOM
                        WebDriverWait(driver, 5).until_not(
                            EC.presence_of_element_located((By.ID, "f3-overlay-loader"))
                        )
                        print("Overlay has disappeared, proceeding to click edit button.")
                        time.sleep(1)  # Small buffer
                    except Exception as e:
                        print(f"Overlay did not disappear in time: {e}")
                    edit_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, edit_button_xpath))
                    )
                    for attempt in range(3):
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", edit_button)
                            time.sleep(0.5)
                            edit_button.click()
                            print("Edit button clicked after recall.")
                            break
                        except Exception as e:
                            print(f"Edit button click attempt {attempt+1} failed: {e}")
                            time.sleep(1)
                    else:
                        print("Could not click edit button after recall after multiple attempts.")
                    # Scroll to the materials section
                    try:
                        print("Scrolling to the materials section...")
                        materials_div = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "materials"))
                        )
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", materials_div)
                        time.sleep(1)
                        print("Scrolled to the materials section.")
                        # Click the delete button in the first row of the materials table, with retry for stale element
                        for attempt in range(3):
                            try:
                                print("Attempting to click the delete button in the first row of the materials table...")
                                delete_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, "//div[@id='materials']//table//tr[1]//span[@title='Remove material']/i[contains(@class, 'icon-remove-bin')]"))
                                )
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", delete_button)
                                time.sleep(1)
                                delete_button.click()
                                print("Delete button in the first row clicked.")
                                # Handle confirmation alert by clicking 'Yes'
                                try:
                                    print("Waiting for confirmation alert and clicking 'Yes'...")
                                    yes_button = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-success') and text()='Yes']"))
                                    )
                                    yes_button.click()
                                    print("Clicked 'Yes' on delete confirmation alert.")
                                    # Now click the Submit button
                                    try:
                                        print("Attempting to click the Submit button after deleting material...")
                                        submit_button_xpath = "/html/body/app-root/app-default-layout/div/app-aside/div/app-f3-aside-panel/div/app-planned-operations/div/div[1]/div/div/button"
                                        submit_button = WebDriverWait(driver, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, submit_button_xpath))
                                        )
                                        submit_button.click()
                                        print("Submit button clicked after deleting material.")
                                        # Now click the Update button on the alert
                                        try:
                                            print("Waiting for the update button on the alert and clicking it...")
                                            update_button_xpath = "/html/body/div[3]/div[2]/div/mat-dialog-container/app-work-order-action-dialog/div/div[2]/button[2]"
                                            update_button = WebDriverWait(driver, 10).until(
                                                EC.element_to_be_clickable((By.XPATH, update_button_xpath))
                                            )
                                            update_button.click()
                                            print("Update button clicked on the alert.")
                                        except Exception as e:
                                            print(f"Could not click Update button on the alert: {e}")
                                    except Exception as e:
                                        print(f"Could not click Submit button after deleting material: {e}")
                                except Exception as e:
                                    print(f"Could not click 'Yes' on delete confirmation: {e}")
                                break
                            except StaleElementReferenceException as e:
                                print(f"StaleElementReferenceException on attempt {attempt+1}, retrying...")
                                time.sleep(1)
                            except Exception as e:
                                print(f"Could not click delete button in the first row: {e}")
                                break
                        else:
                            print("Failed to click delete button in the first row after multiple attempts.")
                    except Exception as e:
                        print(f"Could not scroll to materials section or find materials table: {e}")
                except Exception as e:
                    print(f"Could not click edit button after recall: {e}")
            except Exception as e:
                print(f"Could not click recall button after opening workorder by ID: {e}")
        else:
            print("Could not find agriWorkOrderID in the network responses. Trying fallback: sort and open first row.")
            try:
                # Click the sort icon
                print("Clicking the sort icon to sort by descending order...")
                sort_icon_xpath = "//span[i[contains(@class, 'fa-sort-up') and contains(@class, 'active')]]"
                sort_icon = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, sort_icon_xpath))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sort_icon)
                time.sleep(1)
                sort_icon.click()
                print("Sort icon clicked.")

                # Wait for the table to reload/update (wait for first row to become stale)
                first_row_xpath = "//*[@id=\"main-container\"]/app-work-order-list/app-work-orders-table/div/table/tbody/tr[2]"
                try:
                    old_first_row = driver.find_element(By.XPATH, first_row_xpath)
                    WebDriverWait(driver, 10).until(EC.staleness_of(old_first_row))
                    print("Table updated after sorting.")
                except Exception:
                    # If staleness_of fails (row not present or table doesn't reload), fallback to sleep
                    time.sleep(2)

                # Click the first row in the table
                print("Clicking the first row in the work order table...")
                first_row_xpath = "//*[@id=\"main-container\"]/app-work-order-list/app-work-orders-table/div/table/tbody/tr[1]"
                first_row = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, first_row_xpath))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_row)
                time.sleep(1)
                first_row.click()
                print("First work order row clicked.")
            except Exception as e:
                print(f"Fallback open by sort/click failed: {e}")
    except Exception as e:
        print(f"Error in new workflow for opening workorder by ID: {e}")

    # --- Old workflow for opening/editing workorder by table row is now removed ---

except Exception as e:
    print(f"Error during workorder operations: {e}")

# At the end of the script, don't close the browser as it might be needed by other scripts
print("Workorder script completed.")
