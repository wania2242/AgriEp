import time
import pyotp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException

# --- Configuration ---
EMAIL = "f3admin@circlepfarms.onmicrosoft.com"
PASSWORD = "M89pQ2RVExr3"
TOTP_SECRET = "YRSRDJJVZ6YRNVDH"
LOGIN_URL = (
    "https://businesscentral.dynamics.com/"
    "c4882b6c-58c4-4159-8046-9a8cb8a1d582/"
    "Sandbox-QA?company=PON%20Farms%20LLC&page=89&dc=0&bookmark=19_pwAAAAJ7_0MARgAwADIAMgAwADE"
)

def start_driver():
    """Start Chrome WebDriver with proper options."""
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

def login(driver):
    """Handle login, including email, password, and 2FA with TOTP."""
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 10)

    # Enter email
    try:
        wait.until(EC.visibility_of_element_located((By.ID, "i0116"))).send_keys(EMAIL)
        wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()
    except TimeoutException:
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='email']"))).send_keys(EMAIL)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']"))).click()

    # Enter password
    wait.until(EC.visibility_of_element_located((By.ID, "i0118"))).send_keys(PASSWORD)
    wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()

    # Handle 2FA
    time.sleep(2)
    short_wait = WebDriverWait(driver, 5)
    try:
        short_wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), \"I can't use my Microsoft Authenticator app right now\")]"))).click()
    except TimeoutException:
        pass

    try:
        short_wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Use a verification code')]"))).click()
    except TimeoutException:
        pass

    totp = pyotp.TOTP(TOTP_SECRET).now()
    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='tel' or @type='text']"))).send_keys(totp)

    # Verify
    try:
        verify_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Verify'] | //input[@value='Verify']")))
        driver.execute_script("arguments[0].scrollIntoView(true);", verify_btn)
        verify_btn.click()
    except Exception:
        elems = driver.find_elements(By.XPATH, "//button[normalize-space()='Verify'] | //input[@value='Verify']")
        if elems:
            elems[0].click()
        else:
            raise

    # Stay signed in
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='No']"))).click()
    except:
        pass

def select_growing_cycle(driver):
    """Select 'GROWING CYCLE' value = 2025."""
    wait = WebDriverWait(driver, 20)

    # Switch to main iframe and click New
    wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'iframe')))
    driver.switch_to.frame(driver.find_elements(By.TAG_NAME, 'iframe')[0])

    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='New']"))).click()
        print("[INFO] Clicked 'New' button.")
    except Exception:
        driver.execute_script("document.querySelector('button[aria-label=New]').click();")
        print("[INFO] Clicked 'New' button via JS.")

    time.sleep(3)

    # Switch to iframe containing GROWING CYCLE
    driver.switch_to.default_content()
    for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
        driver.switch_to.frame(iframe)
        if "GROWING CYCLE" in driver.page_source:
            print("[INFO] Found iframe with GROWING CYCLE.")
            break
        driver.switch_to.default_content()

    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@title='Choose a value for GROWING CYCLE']"))).click()
        print("[SUCCESS] Clicked GROWING CYCLE button.")
    except Exception as e:
        print(f"[ERROR] Could not click GROWING CYCLE button: {e}")
        return

    # Find iframe containing 2025
    driver.switch_to.default_content()
    for attempt in range(10):
        time.sleep(2)
        for frm in driver.find_elements(By.TAG_NAME, "iframe"):
            driver.switch_to.frame(frm)
            if "2025" in driver.page_source:
                print("[INFO] Found iframe with '2025'")
                break
            driver.switch_to.default_content()
        else:
            continue
        break
    else:
        raise Exception("[ERROR] Could not find the dimension value list iframe")

    # Click 2025 row
    try:
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//table[contains(@id,'BusinessGrid')]//tr[.//td[normalize-space()='2025']]")
        )).click()
        print("[SUCCESS] Clicked on '2025'")
    except Exception as e:
        print(f"[ERROR] Could not click on 2025 row: {e}")
        raise

    # Click OK
    driver.switch_to.default_content()
    for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
        driver.switch_to.frame(iframe)
        if "OK" in driver.page_source:
            print("[INFO] Found iframe with OK button")
            break
        driver.switch_to.default_content()

    try:
        ok_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='OK']")))
        driver.execute_script("arguments[0].scrollIntoView(true);", ok_button)
        ok_button.click()
        print("[SUCCESS] Clicked OK")
        time.sleep(1)
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Yes']"))).click()
            print("[SUCCESS] Confirmed dimension update.")
        except Exception:
            print("[INFO] No confirmation popup.")
    except Exception as e:
        print(f"[ERROR] OK button not clickable: {e}")

def select_grower(driver):
    """Open Grower lookup, select the first row in the dropdown, and confirm."""
    wait = WebDriverWait(driver, 5)

    # Click Grower lookup (use JS click to avoid overlay intercept)
    grower_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@title='Choose a value for Grower']")))
    try:
        grower_btn.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", grower_btn)
    print("[SUCCESS] Clicked 'Choose a value for Grower'")

    # Wait for the dropdown table to appear (no iframe)
    first_row = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//table[contains(@id,'BusinessGrid')]//tr[1]//a[contains(@title,'Select record')]")
    ))
    driver.execute_script("arguments[0].scrollIntoView(true);", first_row)
    driver.execute_script("arguments[0].click();", first_row)
    print("[SUCCESS] Selected first Grower row via grid row click")

def grower_site(driver):
    
    wait = WebDriverWait(driver, 5)

    # Click Grower lookup (use JS click to avoid overlay intercept)
    growersite_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@title='Choose a value for Growing Site']")))
    try:
        growersite_btn.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", growersite_btn)
    print("[SUCCESS] Clicked 'Choose a value for Growing Site'")
    
    # Wait for the dropdown table to appear (no iframe)
    first_row = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//table[contains(@id,'BusinessGrid')]//tr[1]//a[contains(@title,'Select record')]")
    ))
    driver.execute_script("arguments[0].scrollIntoView(true);", first_row)
    driver.execute_script("arguments[0].click();", first_row)
    print("[SUCCESS] Selected first Grower row via grid row click")

def grower_area(driver):
    
    wait = WebDriverWait(driver, 5)

    # Click Grower lookup (use JS click to avoid overlay intercept)
    growerarea_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@title='Choose a value for Growing Area']")))
    try:
        growerarea_btn.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", growerarea_btn)
    print("[SUCCESS] Clicked 'Choose a value for Growing Area'")
    try:
        JA = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space(text())='JA']")))
        JA.click()
        print("[SUCCESS] Selected 'JA' from lookup")
    except NoSuchElementException:
        print("[ERROR] 'JA' not found in lookup popup")
    except Exception as e:
        print(f"[ERROR] Unexpected error while selecting 'JA': {e}")
    time.sleep(2)

def grower_plot(driver):
    wait = WebDriverWait(driver, 5)
    growerplot_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@title='Choose a value for Growing Plot']")))
    print(f"[INFO] Found 'Choose a value for Growing Plot' button: {growerplot_btn}, displayed: {growerplot_btn.is_displayed()}, enabled: {growerplot_btn.is_enabled()}")

    # Focus the button
    driver.execute_script("arguments[0].focus();", growerplot_btn)
    time.sleep(1)
    try:
        growerplot_btn.click()
        print("[INFO] Clicked with .click()")
    except Exception as e:
        print(f"[WARN] .click() failed: {e}, trying JS click")
        driver.execute_script("arguments[0].click();", growerplot_btn)
        print("[INFO] Clicked with JS click")
    # Try dispatching a mousedown event
    driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));", growerplot_btn)
    print("[INFO] Dispatched mousedown event")
    time.sleep(2)
    # Check if dropdown appeared
    dropdown_present = len(driver.find_elements(By.XPATH, "//table[contains(@id,'BusinessGrid')]//tr")) > 0
    print(f"[DEBUG] Dropdown present after click: {dropdown_present}")
    if not dropdown_present:
        print("[ERROR] Dropdown did not open after clicking the button.")
    else:
        try:
            plot= wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space(text())='45I034SW']")))
            plot.click()
            print("[SUCCESS] Selected '45I034SW' from lookup")
        except NoSuchElementException:
            print("[ERROR] '45I034SW' not found in lookup popup")
        except Exception as e:
            print(f"[ERROR] Unexpected error while selecting 'CORN YELL': {e}")
    
    time.sleep(2)

def grower_item(driver):
    wait = WebDriverWait(driver, 5)

    # Click Grower lookup
    groweritem_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@title='Choose a value for Growing Item No.']")))
    try:
        groweritem_btn.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", groweritem_btn)
    print("[SUCCESS] Clicked 'Choose a value for Growing Item No.'")

    # Wait for the popup to load and select 'CORN YELL'
    try:
        corn_yell_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space(text())='CORN YELL']")))
        corn_yell_option.click()
        print("[SUCCESS] Selected 'CORN YELL' from lookup")
    except NoSuchElementException:
        print("[ERROR] 'CORN YELL' not found in lookup popup")
    except Exception as e:
        print(f"[ERROR] Unexpected error while selecting 'CORN YELL': {e}")
    
    time.sleep(2)

def enter_value_by_id(driver, element_id, value):
    """
    Enter a value into an input field by its ID, triggering all necessary events.
    """
    wait = WebDriverWait(driver, 30)
    try:
        input_elem = wait.until(EC.visibility_of_element_located((By.ID, element_id)))
        print(f"Element found (id={element_id}):", input_elem.is_displayed(), input_elem.is_enabled())

        # Clear the field first
        input_elem.clear()

        # Set value via JavaScript
        driver.execute_script("arguments[0].value = arguments[1];", input_elem, value)

        # Trigger input and change events so the page notices the change
        driver.execute_script("""
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, input_elem)

        # Optionally, trigger Enter key press using JavaScript
        driver.execute_script("""
            var e = new KeyboardEvent('keydown', {key:'Enter', keyCode:13, which:13, bubbles:true});
            arguments[0].dispatchEvent(e);
        """, input_elem)

        print(f"[SUCCESS] Entered value '{value}' in element with id '{element_id}' and triggered events.")
        time.sleep(2)
    except Exception as e:
        print(f"[ERROR] Could not enter value in element with id '{element_id}': {e}")

def click_tasks_line_agri_master(driver):
    wait = WebDriverWait(driver, 5)  # Increased timeout for potentially slow loading
    try:
        # Step 1: Click "Tasks"
        print("[INFO] Looking for 'Tasks' button...")
        tasks_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@role='button' and .//span[@title='Tasks']]")))
        tasks_btn.click()
        print("[SUCCESS] Clicked on 'Tasks'")

        # Step 2: Click "Line" button
        print("[INFO] Waiting for 'Line' button to appear...")
        line_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Line' or .//span[text()='Line']]")))
        try:
            line_btn.click()
        except StaleElementReferenceException:
            print("[WARN] StaleElementReferenceException for Line button, re-finding...")
            line_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Line' or .//span[text()='Line']]")))
            line_btn.click()
        print("[SUCCESS] Clicked on 'Line' button")

        # Step 3: Click "Agri Functions"
        print("[INFO] Waiting for 'Agri Functions' button to appear...")
        agri_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Agri Functions' or .//span[@aria-label='Agri Functions']]")))
        print(f"[INFO] Agri Functions button found: Displayed={agri_btn.is_displayed()}, Enabled={agri_btn.is_enabled()}")
        try:
            time.sleep(2)
            agri_btn.click()
            print("[INFO] Clicked 'Agri Functions' with .click()")
        except ElementClickInterceptedException:
            print("[WARN] ElementClickInterceptedException on 'Agri Functions', trying JS click.")
            driver.execute_script("arguments[0].click();", agri_btn)
            print("[INFO] Clicked 'Agri Functions' with JS click.")
        except Exception as e:
            print(f"[WARN] General exception clicking 'Agri Functions' with .click(): {e}. Trying JS click.")
            driver.execute_script("arguments[0].click();", agri_btn)
            print("[INFO] Clicked 'Agri Functions' with JS click.")

        # Step 4: Click "Master Task"
        print("[INFO] Waiting for 'Master Task' button to be present in dropdown...")
        master_task_btn_present = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Master Task' or @title='Master Task' or .//div[text()='Master Task']]")))
        print("[SUCCESS] 'Master Task' button is present.")
        print("[INFO] Waiting for 'Master Task' button to be clickable...")
        master_task_btn_clickable = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Master Task' or @title='Master Task' or .//div[text()='Master Task']]")))
        try:
            master_task_btn_clickable.click()
        except StaleElementReferenceException:
            print("[WARN] StaleElementReferenceException for Master Task button, re-finding before final click...")
            master_task_btn_final = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Master Task' or @title='Master Task' or .//div[text()='Master Task']]")))
            master_task_btn_final.click()
        print("[SUCCESS] Clicked on 'Master Task' button")

        # Step 5: Click the relevant task
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//table[contains(@id,'BusinessGrid')]//tr[.//td[normalize-space()='Early Spray Corn VR']]")
            )).click()
            print("[SUCCESS] Selected the row with 'Early Spray Corn VR' by clicking its description cell in the main DOM.")
        except Exception as e:
            print(f"[ERROR] Clicking the description cell for 'Early Spray Corn VR' failed in the main DOM: {e}")

        # Step 6: Click "Actions" button
        print("[INFO] Waiting for 'Actions' button to be clickable...")
        actions_button_xpath = "//button[@aria-label='Actions']"
        actions_button_element = wait.until(EC.element_to_be_clickable((By.XPATH, actions_button_xpath)))
        try:
            time.sleep(2)
            actions_button_element.click()
            print("[SUCCESS] Clicked on 'Actions' button.")
        except Exception as e:
            print(f"[ERROR] Clicking 'Actions' button failed: {e}")

        # Step 7: Click "Import lines to job"
        print("[INFO] Waiting for 'Import lines to job' button to be clickable in dropdown...")
        import_lines_xpath = "//button[@aria-label='Import lines to job' or @title='Import lines to job' or .//div[text()='Import lines to job']]"
        import_lines_clickable = wait.until(EC.element_to_be_clickable((By.XPATH, import_lines_xpath)))
        try:
            import_lines_clickable.click()
        except StaleElementReferenceException:
            print("[WARN] StaleElementReferenceException for Import lines to job button, re-finding before final click...")
            import_lines_clickable = wait.until(EC.element_to_be_clickable((By.XPATH, import_lines_xpath)))
            import_lines_clickable.click()
        print("[SUCCESS] Clicked on 'Import lines to job' button")

        # Step 8: Click OK after import
        try:
            ok_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='OK']")))
            driver.execute_script("arguments[0].scrollIntoView(true);", ok_button)
            ok_button.click()
            print("[SUCCESS] Clicked OK button after import.")
            time.sleep(1)
        except Exception as e:
            print(f"[ERROR] OK button after import not clickable: {e}")

        # Step 9: Click Back button (updated)
        print("[INFO] Waiting for 'Back' button to be clickable...")
        back_button_xpath = "//button[contains(@class,'back-button') and (@title='Back' or @aria-label='Back')]"
        try:
            back_button_element = wait.until(EC.element_to_be_clickable((By.XPATH, back_button_xpath)))
            driver.execute_script("arguments[0].scrollIntoView(true);", back_button_element)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", back_button_element)
            print("[SUCCESS] Clicked on 'Back' button using JS click.")
        except Exception as e:
            print(f"[ERROR] Clicking 'Back' button failed: {e}")

    except TimeoutException as e:
        print("[ERROR] Timeout waiting for one of the elements in click_tasks_line_agri_master:", str(e))
    except Exception as e:
        print("[FATAL] Unexpected error occurred in click_tasks_line_agri_master:", str(e))
def select_sync_to_farm(driver):
    wait = WebDriverWait(driver, 5)

    try:
        # Wait for the <select> element using XPath
        dropdown_element = wait.until(EC.presence_of_element_located((
            By.XPATH, "//select[contains(@title, 'In Progress')]"
        )))

        # Wrap it in a Select object
        select = Select(dropdown_element)

        # Select option by visible text
        select.select_by_visible_text("Sync to Farm App")

        print("[SUCCESS] Selected 'Sync to Farm App' from dropdown.")

    except Exception as e:
        print(f"[ERROR] Failed to select dropdown option: {e}")

if __name__ == "__main__":
    driver = start_driver()
    try:
        login(driver)
        select_growing_cycle(driver)
        select_grower(driver)
        grower_site(driver)
        grower_area(driver)
        grower_plot(driver)
        grower_item(driver)
        enter_value_by_id(driver, "blyee", "1")
        enter_value_by_id(driver, "bm4ee", "10")
        click_tasks_line_agri_master(driver)
        select_sync_to_farm(driver)
        time.sleep(1)
        # select_sync_to_farm(driver)
        driver.switch_to.default_content()
    except Exception as e:
        print(f"[FATAL] Script failed: {e}")
    finally:
        driver.quit()
