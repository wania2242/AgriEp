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

try:
    # Step 1: Visit the website
    try:
        login_url = "https://agrierp-eh-pon-farms-qa-dfedaqg0hegranhf.eastus-01.azurewebsites.net/login"
        driver.get("https://agrierp-eh-pon-farms-qa-dfedaqg0hegranhf.eastus-01.azurewebsites.net/")
        test_reporter.log_success("Visited main site")
    except Exception as e:
        test_reporter.log_failure("Visit main site failed", e)
        raise

    if "/login" in driver.current_url:
        # Step 2: Click login button
        try:
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-login"))).click()
            test_reporter.log_success("Login button clicked")
        except Exception as e:
            test_reporter.log_failure("Login button click failed", e)
            raise
        # Step 3: Microsoft login page
        try:
            WebDriverWait(driver, 5).until(EC.url_contains("login.microsoftonline.com"))
            test_reporter.log_success("MS login page loaded")
        except Exception as e:
            test_reporter.log_failure("MS login page load failed", e)
            raise
        # Step 4: Email input
        try:
            css_selectors = "#i0116, input[name='loginfmt'], input[type='email'], input[type='text']"
            email_input = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selectors))
            )
            email_input.clear()
            email_input.send_keys("circlepfarms@circlepfarms.onmicrosoft.com")
            email_input.send_keys(Keys.RETURN)
            test_reporter.log_success("Email entered and submitted")
        except Exception as e:
            test_reporter.log_failure("Email input failed", e)
            raise
        # Step 5: Password input
        try:
            password_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "i0118")))
            password_input.send_keys("Naco682917")
            password_input.send_keys(Keys.RETURN)
            test_reporter.log_success("Password entered and submitted")
        except Exception as e:
            test_reporter.log_failure("Password input failed", e)
            raise
        # Step 6: Sign-in button
        try:
            sign_in_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "idSIButton9"))
            )
            sign_in_button.click()
            test_reporter.log_success("Sign-in button clicked")
        except Exception as e:
            test_reporter.log_failure("Sign-in button click failed", e)
            raise
        # Step 7: OTP/2FA
        try:
            totp = pyotp.TOTP("fv7jgtcf2lg6hrhn")
            otp_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "idTxtBx_SAOTCC_OTC"))
            )
            submit_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
            )
            auth_code = totp.now()
            otp_input.clear()
            otp_input.send_keys(auth_code)
            submit_btn.click()
            test_reporter.log_success("OTP entered and submitted")
        except Exception as e:
            test_reporter.log_failure("OTP/2FA failed", e)
            raise
        # Step 8: Stay signed in prompt
        try:
            yes_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "idSIButton9"))
            )
            yes_button.click()
            test_reporter.log_success("Stay signed in prompt handled")
        except Exception as e:
            test_reporter.log_failure("Stay signed in prompt failed", e)
        # Step 9: Final redirect
        try:
            WebDriverWait(driver, 15).until(
                EC.url_contains("agrierp-eh-pon-farms-qa-dfedaqg0hegranhf.eastus-01.azurewebsites.net")
            )
            test_reporter.log_success("Redirected to app after login")
        except Exception as e:
            test_reporter.log_failure("Redirect to app after login failed", e)
            raise
    else:
        test_reporter.log_success("Already logged in, skipping login steps")
except Exception as e:
    print(f"[FATAL] Script failed: {e}")
finally:
    pass

print("\nLogin script completed.")
print("-------------------------")