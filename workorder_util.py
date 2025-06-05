import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

def plot_selection_and_save(driver): 
        # Click the button to open plot selection
        plot_button_xpath = "//*[@id='blocks']/app-work-order-activity-table/div[1]/div[2]/div[2]/button[2]"
        plot_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, plot_button_xpath))
        )
        plot_button.click()
        print("Plot selection button clicked.")
        # Now select the plot checkbox
        plot_checkbox_xpath = "/html/body/app-root/app-default-layout/div/app-aside/div/app-f3-aside-panel/div/app-planned-operations/app-all-blocks-type/div/div/div[3]/table/tbody/tr[1]/td[1]/input"
        plot_checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, plot_checkbox_xpath))
        )
        plot_checkbox.click()
        print("Plot checkbox clicked.")

        # Click the Save button after selecting the plot
        try:
            plot_save_button_xpath = "/html/body/app-root/app-default-layout/div/app-aside/div/app-f3-aside-panel/div/app-planned-operations/app-all-blocks-type/div/div/div[1]/div[2]/button"
            plot_save_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, plot_save_button_xpath))
            )
            plot_save_button.click()
            print("Plot Save button clicked after plot selection.")
            time.sleep(1)
        except Exception as e:
            print(f"Could not click plot Save button after plot selection: {e}")