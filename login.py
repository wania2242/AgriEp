from shared_driver import get_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import pickle
import datetime
import json
import shutil
import pyotp
import test_reporter

# Always create a new Selenium driver instance for a fresh session
driver = get_driver()

# Step 1: Visit the website

# Visit the main site
login_url = "https://agrierp-eh-pon-farms-qa-dfedaqg0hegranhf.eastus-01.azurewebsites.net/login"
driver.get("https://agrierp-eh-pon-farms-qa-dfedaqg0hegranhf.eastus-01.azurewebsites.net/")


# If not redirected to /login, skip the rest of the script
if "/login" in driver.current_url:
    try:
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-login"))).click()
        test_reporter.log_success("Login button clicked.", source='login')
        # Step 3: detect Microsoft login page in same or new window
        try:
            WebDriverWait(driver, 5).until(EC.url_contains("login.microsoftonline.com"))
            test_reporter.log_success("MS login page loaded", source='login')
        except:
            orig = driver.current_window_handle
            WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
            for handle in driver.window_handles:
                if handle != orig:
                    driver.switch_to.window(handle)
                    print("Switched to MS login window:", driver.current_url)
                    break
    except Exception as e:
        test_reporter.log_failure("Failed to trigger login flow", e, source='login')

    # Step 4: Wait for and fill in the email field robustly
    try:
        time.sleep(2)
        css_selectors = "#i0116, input[name='loginfmt'], input[type='email'], input[type='text']"
        email_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selectors))
        )
        email_input.clear()
        email_input.send_keys("circlepfarms@circlepfarms.onmicrosoft.com")
        email_input.send_keys(Keys.RETURN)
        test_reporter.log_success("Email field submitted", source='login')
    except Exception as e:
        test_reporter.log_failure("Failed to locate or submit email field", e, source='login')
        # Debug: list all input elements and their attributes
        try:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            print(f"Found {len(inputs)} input elements on page:")
            for inp in inputs:
                print({
                    "id": inp.get_attribute("id"),
                    "name": inp.get_attribute("name"),
                    "type": inp.get_attribute("type"),
                    "placeholder": inp.get_attribute("placeholder")
                })
        except Exception as dbg_e:
            print("Error listing input elements:", dbg_e)

    # Step 5: Wait for the password field to appear (if needed)
    try:
        password_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "i0118")))
        password_input.send_keys("Naco682917")  # Replace with actual password
        password_input.send_keys(Keys.RETURN)  # Submit the password field
        test_reporter.log_success("Password entered and submitted", source='login')
    except Exception as e:
        test_reporter.log_failure("Failed to locate or submit password field", e, source='login')

    # Step 6: Enhanced approach to clicking the Sign-in button
    try:
        # Capture current URL before attempting to click
        current_url_before = driver.current_url
        print("URL before click:", current_url_before)
        
        # Add a short wait to make sure page is fully loaded
        time.sleep(2)
        
        # Try multiple methods to click the button with verification
        methods_tried = 0
        click_success = False
        
        # Method 1: Find the button again (to avoid stale element) and try standard click
        print("Standard click with fresh element...")
        try:
            # Use element_to_be_clickable instead of just presence
            sign_in_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "idSIButton9"))
            )
            sign_in_button.click()
            
            # Verify if click worked by checking URL change or page title change
        ##  time.sleep(2)  # Wait for page to potentially change
            if driver.current_url != current_url_before or "Sign in to your account" not in driver.title:
                print("Standard click verified successful - URL or title changed.")
                click_success = True
            else:
                print("Standard click reported success but UI didn't change.")
        except Exception as click_error:
            print("Standard click failed:", click_error)
        # If we get to a new page or a new prompt appears, let's see what's there
        if click_success:
            # Now we should be at the OTP screen or somewhere new
            print("\nFinal navigation check:")
            print("Current URL:", driver.current_url)
            print("Page Title:", driver.title)
            print("Current page source snippet:", driver.page_source[:300], "...")
            
        # Handle Google Authenticator verification
        try:
            # First verify we're on an OTP page
            verify_text = driver.find_elements(By.XPATH, "//*[contains(text(), 'verification') or contains(text(), 'code') or contains(text(), 'authenticator') or contains(text(), 'OTP')]")
            
            if verify_text:
                print("\nDetected verification page! Found text related to verification/OTP")
                print("Taking screenshot of verification page...")
                driver.save_screenshot("verification_page.png")
                totp = pyotp.TOTP("fv7jgtcf2lg6hrhn")
                # Find and fill the OTP input field
                otp_field_found = False
                try:
                    # Look for OTP input fields
                    otp_input = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "idTxtBx_SAOTCC_OTC"))
                        )
                    otp_field_found = True
                    try:
                        submit_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
                        )
                        print(f"Found verification submit button")
                        auth_code = totp.now()
                        print(f"Generated TOTP code: {auth_code}")
                        # Clear field if needed and input the code
                        otp_input.clear()
                        otp_input.send_keys(auth_code)
                        print(f"Entered authentication code: {auth_code}")
                        test_reporter.log_success("Entered authentication code", source='login')
                        submit_btn.click()
                        print("Clicked verification submit button")
                        test_reporter.log_success("Clicked verification submit button", source='login')
                        time.sleep(3)  # Wait for submission
                        # Check for "Stay signed in" prompt which may appear next
                        try:        
                            # Look for the Yes button more broadly
                            yes_button_locators = [
                                (By.ID, "idSIButton9"),  # Standard Microsoft ID
                                (By.XPATH, "//button[contains(text(), 'Yes')]"),  # Button containing 'Yes'
                                (By.XPATH, "//input[@value='Yes']"),  # Input with value 'Yes'
                                (By.XPATH, "//button[contains(@class, 'primary')]")  # Primary button (usually Yes/Accept)
                            ]
                            
                            for by_method, locator in yes_button_locators:
                                try:
                                    yes_button = WebDriverWait(driver, 3).until(
                                        EC.element_to_be_clickable((by_method, locator))
                                    )
                                    print(f"Found 'Stay signed in' prompt, clicking button with locator: {locator}")
                                    yes_button.click()
                                    print("Clicked button on 'Stay signed in' prompt")
                                    time.sleep(2)  # Wait for click to take effect
                                    test_reporter.log_success("Clicked 'Stay signed in' prompt", source='login')
                                    break
                                except Exception:
                                    continue
                                    
                        except Exception as stay_error:
                            test_reporter.log_failure("No 'Stay signed in' prompt found or failed to interact with it", stay_error, source='login')
                                
                        try:    
                            time.sleep(2)  # Wait briefly for Microsoft login window to close
                            # Step 1: Switch back to main app window
                            for handle in driver.window_handles:
                                driver.switch_to.window(handle)
                                if "agrierp-eh-pon-farms-qa-dfedaqg0hegranhf.eastus-01.azurewebsites.net" in driver.current_url:
                                    print(f"✅ Switched to main window: {driver.current_url}")
                                    break

                            # Step 2: Wait until page is fully redirected
                            WebDriverWait(driver, 15).until(
                                EC.url_contains("agrierp-eh-pon-farms-qa-dfedaqg0hegranhf.eastus-01.azurewebsites.net")
                            )
                            print("✅ Successfully redirected to app")
                        except Exception as redirect_error:
                            print("Error waiting for redirect to main app:", redirect_error)        

                        # Check if URL changed after submitting
                        if driver.current_url != current_url_before:
                            print("\nVerification successful! URL changed after submitting code.")
                    except Exception as input_err:
                        print(f"Error interacting with OTP field: {input_err}")
                        test_reporter.log_failure("Error interacting with OTP field", input_err, source='login')
                except Exception as find_err:
                    print(f"Error finding OTP fields with {locator}: {find_err}")
                    test_reporter.log_failure("Error finding OTP fields", find_err, source='login')
            
                if not otp_field_found:
                    print("\nCould not find OTP input field. Taking screenshot for debugging.")
                    test_reporter.log_failure("Could not find OTP input field", source='login')
                    driver.save_screenshot("otp_page_not_found.png")
                    print("Page source snippet:", driver.page_source[:500], "...")
            else:
                print("\nNo verification page detected. Might have already been authenticated or verification is not required.")
        
        except Exception as otp_error:
            print("\nError handling verification page:", otp_error)
            driver.save_screenshot("verification_error.png")

    except Exception as e:
        print("All sign-in button approaches failed:", e)
        
        # Try alternative approach: locate any submit buttons or links on the page
        print("\nFallback approach: Trying to identify ALL interactive elements...")
        
        # Save page source for debugging
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Saved page source to page_source.html for inspection")
        
        # Try a broader approach to find all possible interactive elements
        interactive_elements = [
            (By.TAG_NAME, "button"),  # All buttons
            (By.TAG_NAME, "a"),  # All links
            (By.CSS_SELECTOR, "input[type='submit']"),  # Submit inputs
            (By.CSS_SELECTOR, "input[type='button']"),  # Button inputs
            (By.XPATH, "//*[contains(@class, 'button')]"),  # Elements with 'button' in class
            (By.XPATH, "//*[contains(@class, 'btn')]"),  # Elements with 'btn' in class
            (By.XPATH, "//*[contains(@class, 'submit')]")  # Elements with 'submit' in class
        ]

        # Try clicking every interactive element we find to see if any works
        for by_method, locator in interactive_elements:
            try:
                elements = driver.find_elements(by_method, locator)
                print(f"Found {len(elements)} elements with locator: {locator}")
                
                for i, element in enumerate(elements):
                    try:
                        # Get properties for debugging
                        element_text = element.text if element.text else "[No text]"
                        element_id = element.get_attribute("id") if element.get_attribute("id") else "[No ID]"
                        element_class = element.get_attribute("class") if element.get_attribute("class") else "[No class]"
                        
                        print(f"Element {i}: Text='{element_text}', ID='{element_id}', Class='{element_class}'")
                        
                        # If this looks like a sign-in button, try clicking it
                        if ("sign" in element_text.lower() or 
                            "next" in element_text.lower() or 
                            "continue" in element_text.lower() or 
                            "submit" in element_text.lower() or
                            "sign" in element_id.lower()):
                            
                            print(f"This looks like a sign-in element! Attempting to click...")
                            element.click()
                            
                            # Wait and verify if the page changed
                            time.sleep(2)
                            if driver.current_url != current_url_before:
                                print(f"Success! Clicked element and page URL changed!")
                                break  # Exit the current loop, not return
                    except Exception as click_err:
                        print(f"Error interacting with element {i}: {click_err}")
                        continue
            except Exception as find_err:
                print(f"Error finding elements with {locator}: {find_err}")
                continue
else:
    print(f"Already logged in (current URL: {driver.current_url}), skipping login steps.")
print("\nLogin script completed.")
print("-------------------------")
