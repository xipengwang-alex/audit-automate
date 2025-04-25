# retailers/homedepot.py
import time
import random
import os
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Tuple # Added for type hinting

# Import core functions
from core.browser_setup import setup_browser
from core.screenshot_manager import take_full_page_screenshot, extract_page_text
from core.image_utils import crop_screenshot

class HomeDepotAuditor:
    """Auditor implementation specific to Home Depot."""

    RETAILER_NAME = "homedepot"
    # Updated path to prompts directory
    PROMPT_PATH = os.path.join("prompts", "prompt_homedepot.txt")

    def get_prompt_path(self) -> str:
        return self.PROMPT_PATH

    def _handle_popups(self, driver):
        """Handles Home Depot specific popups (e.g., cookies)."""
        try:
            # OneTrust Cookie Consent
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            # Scroll slightly to ensure the button is not obscured
            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", cookie_button)
            time.sleep(0.5)
            actions = webdriver.ActionChains(driver)
            # More robust click attempt
            actions.move_to_element(cookie_button).click().perform()
            print("Closed cookie consent popup (Home Depot)")
            time.sleep(random.random() * 2)
        except Exception:
            print("No Home Depot cookie popup detected or timed out.")
        # Add handling for other potential HD popups here if needed

    def _find_and_expand_details(self, driver):
        """Finds and clicks the 'Product Details' section on Home Depot."""
        total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
        found_details_button = False
        details_button = None
        current_position = 0
        max_scroll_attempts = 20
        scroll_attempts = 0
        detail_selectors = [
            # New selector based on user input (PRIORITIZED)
            "//div[@class='navlink-pso' and normalize-space(.)='Product Details']",
            # Original selectors as fallbacks
            "//button[normalize-space(.)='Product Details']",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'product details')]",
            "//button[@data-testid='product-details-accordion-button']",
            "//div[@id='product-details__panel--container']//button",
            "//a[normalize-space(.)='View More Details']",
            "//div[contains(@class, 'accordion-title') and contains(., 'Details')]"
        ]
        scroll_increment = 300

        print("Searching for Product Details button/link (Home Depot)...")
        while not found_details_button and scroll_attempts < max_scroll_attempts and current_position < total_height:
            for selector in detail_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            element_text = element.text.lower() if element.text else ""
                            tag_name = element.tag_name.lower()
                            # Improved filtering
                            if 'add to' not in element_text and 'cart' not in element_text and 'list' not in element_text:
                                # Check if it's the div or seems like a details expander
                                if (tag_name == 'div' and 'product details' in element_text) or \
                                   ('detail' in element_text or 'spec' in element_text or 'view more' in element_text):
                                    details_button = element
                                    found_details_button = True
                                    print(f"Found target details element: <{tag_name}> '{element.text}' using selector: {selector}")
                                    # --- BREAK INNER LOOP once found ---
                                    break
                    # --- BREAK OUTER LOOP once found ---
                    if found_details_button: break
                except Exception as find_err:
                    # print(f"Selector error ({selector}): {find_err}") # Optional debug
                    continue
            # --- BREAK WHILE LOOP once found ---
            if found_details_button: break

            scroll_attempts += 1
            current_position += scroll_increment
            driver.execute_script(f"window.scrollTo(0, {min(current_position, total_height)});")
            time.sleep(1.5 + random.random())

        # Attempt to click if found
        if found_details_button:
            try:
                print(f"Attempting to click details element: <{details_button.tag_name}> '{details_button.text}'")
                # Scroll element into view smoothly, centered
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'});", details_button)
                time.sleep(1.5) # Wait for scroll
                # Use JS click for reliability against overlays
                driver.execute_script("arguments[0].click();", details_button)
                print("Clicked details element using JavaScript.")
                time.sleep(3 + random.random()) # Wait for content to potentially load/expand
                return True
            except Exception as click_err:
                print(f"Could not click details element: {click_err}")
                try: driver.find_element(By.TAG_NAME, 'body').click() # Click body to potentially remove focus issues
                except: pass
                return False
        else:
            print("Could not find Product Details button/link (Home Depot).")
            return False
        
    def capture_product_data(self, url: str, output_base_filename: str) -> Tuple[bool, str]:
        """Captures screenshot and text for a Home Depot product page."""
        output_png = f"{output_base_filename}.png"
        output_txt = f"{output_base_filename}.txt"
        print(f"Starting Home Depot capture for: {url}")

        driver = None
        try:
            driver = setup_browser()
            driver.get(url)
            print("Waiting for page load...")
            time.sleep(5 + random.random() * 2)

            self._handle_popups(driver)
            time.sleep(1 + random.random())

            details_opened = self._find_and_expand_details(driver)
            if not details_opened: print("Warning: Failed to open product details section.")
            else: print("Product details section interaction attempted.")

            screenshot_success = take_full_page_screenshot(driver, output_png)
            text_success = extract_page_text(driver, output_png)

            if not screenshot_success or not text_success:
                 print("Warning: Screenshot or text extraction might be incomplete.")

            crop_success = crop_screenshot(output_png)
            if not crop_success: print("Warning: Screenshot cropping failed.")

            driver.quit()
            print(f"Home Depot capture finished for: {url}")
            return True, ""

        except Exception as e:
            error_msg = f"Error during Home Depot capture for {url}: {str(e)}"
            print(f"ERROR: {error_msg}")
            if driver: driver.quit()
            if os.path.exists(output_png): os.remove(output_png)
            if os.path.exists(output_txt): os.remove(output_txt)
            return False, error_msg