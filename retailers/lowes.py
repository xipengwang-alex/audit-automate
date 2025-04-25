# retailers/lowes.py
import time
import random
import os
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Tuple # Added for type hinting

# Import core functions
from core.browser_setup import setup_browser
from core.screenshot_manager import take_full_page_screenshot, extract_page_text
from core.image_utils import crop_screenshot

class LowesAuditor:
    """Auditor implementation specific to Lowe's."""

    RETAILER_NAME = "lowes"
    PROMPT_PATH = os.path.join("prompts", "prompt_lowes.txt")

    def get_prompt_path(self) -> str:
        return self.PROMPT_PATH

    def _handle_popups(self, driver):
        """Handles Lowe's specific popups."""
        print("Handling popups (Lowe's)...")
        popup_selectors = [
            "//button[contains(@aria-label, 'close')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
            "//div[@role='dialog']//button[contains(@class, 'close')]", # Close button within a dialog
            "//button[@id='closeButton']" # Common ID sometimes used
        ]
        for selector in popup_selectors:
            try:
                # Use a short wait for each potential popup
                close_button = WebDriverWait(driver, 3).until(
                     EC.element_to_be_clickable((By.XPATH, selector))
                 )
                driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", close_button)
                time.sleep(0.5)
                close_button.click()
                print(f"Clicked a potential popup close button using selector: {selector}")
                time.sleep(1) # Wait a moment after closing
                # Assume one popup closed is enough for now, could check for more
                # break
            except TimeoutException:
                 # Element not found or not clickable within timeout, continue checking others
                 # print(f"Popup selector not found/clickable: {selector}") # Optional debug
                 pass
            except Exception as e:
                 print(f"Error clicking popup button ({selector}): {e}")
                 # Continue trying other selectors

    def _click_view_all_images(self, driver) -> bool:
        """Finds and clicks the 'View All Images' button if present."""
        try:
            print("Searching for 'View All Images' button (Lowe's)...")
            # Wait for the button to be present using its ID
            view_all_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "galleryExpandBtn"))
            )
            print("Found 'View All Images' button.")

            # Scroll to the button and click using JavaScript
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", view_all_button)
            time.sleep(1) # Wait for scroll animation
            driver.execute_script("arguments[0].click();", view_all_button)
            print("Clicked 'View All Images' button.")
            time.sleep(2 + random.random()) # Wait for gallery to potentially open/load
            return True
        except TimeoutException:
            print("Timed out waiting for 'View All Images' button.")
            return False
        except NoSuchElementException:
             print("'View All Images' button not found.")
             return False
        except Exception as e:
            print(f"Error clicking 'View All Images' button: {e}")
            return False

    def capture_product_data(self, url: str, output_base_filename: str) -> Tuple[bool, str]:
        """
        Captures screenshot and text for a Lowe's product page.
        Does NOT crop the final screenshot.

        Args:
            url (str): The product URL.
            output_base_filename (str): Base path for output files (e.g., "output/link2_lowes").

        Returns:
            Tuple[bool, str]: (Success status, Error message)
        """
        output_png = f"{output_base_filename}.png"
        output_txt = f"{output_base_filename}.txt"
        print(f"Starting Lowe's capture for: {url}")

        driver = None
        try:
            driver = setup_browser()
            driver.get(url)
            print("Waiting for page load...")
            time.sleep(7 + random.random() * 4) # Initial wait

            self._handle_popups(driver)
            time.sleep(1 + random.random())

            self._click_view_all_images(driver) # Attempt to click view all images

            # Take screenshot and extract text
            screenshot_success = take_full_page_screenshot(driver, output_png)
            text_success = extract_page_text(driver, output_png)

            if not screenshot_success or not text_success:
                 print("Warning: Screenshot or text extraction might be incomplete.")

            driver.quit()
            print(f"Lowe's capture finished for: {url}")
            return True, ""

        except Exception as e:
            error_msg = f"Error during Lowe's capture for {url}: {str(e)}"
            print(f"ERROR: {error_msg}")
            if driver: driver.quit()
            if os.path.exists(output_png): os.remove(output_png)
            if os.path.exists(output_txt): os.remove(output_txt)
            return False, error_msg