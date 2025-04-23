# c:\Users\wangx\Dropbox\Purdue\APEC Water\audit-automate\link_processor.py
import os
import time
import random
from browser_setup import setup_browser, handle_cookie_popup
from details_finder import find_product_details_button, click_details_button
from screenshot_manager import take_full_page_screenshot, extract_page_text
from image_utils import crop_screenshot
from reporting_utils import report
from typing import List, Optional # Import typing helpers

def take_product_screenshot(url, output_filename="product_details.png"):
    """
    Navigate to a Home Depot product page, expand the product details tab,
    and take a full-page screenshot.
    
    Args:
        url (str): The Home Depot product URL
        output_filename (str): Filename to save the screenshot
        
    Returns:
        tuple: (success, error_message, details_opened)
    """
    print(f"Navigating to: {url}")
    
    # Initialize browser
    try:
        driver = setup_browser()
    except Exception as e:
        error_msg = f"Failed to initialize browser: {str(e)}"
        print(f"ERROR: {error_msg}")
        return False, error_msg, False
    
    # Track if product details tab was successfully opened
    details_opened = False
    
    try:
        # Navigate to the URL
        driver.get(url)
        
        # Wait for the page to load with random delay to appear more human-like
        print("Waiting for page to load...")
        time.sleep(5 + (random.random() * 2))  # 5-7 second delay
        
        # Perform some random scrolling to appear more human-like
        random_scroll_times = random.randint(2, 4)
        for _ in range(random_scroll_times):
            scroll_amount = random.randint(100, 300)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(0.5 + (random.random() * 1))  # 0.5-1.5 second delay
        
        # Handle cookie consent popup if present
        handle_cookie_popup(driver)
        
        # First, scroll down the page to find the Product Details area
        print("Scrolling page slowly to locate Product Details section...")
        found_button, button_element, total_height = find_product_details_button(driver)
        
        # Try to click the Product Details tab
        print("Attempting to click Product Details tab...")
        click_details_button(driver, found_button, button_element, total_height)
        
        # Set details_opened based on whether the button was found and clicked
        details_opened = found_button
        
        if not details_opened:
            print("WARNING: Product Details tab could not be located or clicked")
        
        # Wait for product details to load after clicking
        print("Waiting for product details to expand...")
        time.sleep(3 + (random.random() * 2))  # 3-5 second delay
        
        # Take a full page screenshot
        screenshot_success = take_full_page_screenshot(driver, output_filename)
        if not screenshot_success:
            print("WARNING: Screenshot may not be complete")
        
        # IMPORTANT: Extract text AFTER product details are expanded
        print("Extracting page text with expanded product details...")
        text_success = extract_page_text(driver, output_filename)
        if not text_success:
            print("WARNING: Text extraction may not be complete")
        
    except Exception as e:
        error_msg = f"An error occurred during page processing: {str(e)}"
        print(f"ERROR: {error_msg}")
        driver.quit()
        return False, error_msg, details_opened
    
    try:
        # Crop the screenshot to remove bottom 1/3
        crop_success = crop_screenshot(output_filename)
        if not crop_success:
            print("WARNING: Screenshot cropping may not be complete")
        
    except Exception as e:
        error_msg = f"Error in post-processing: {str(e)}"
        print(f"ERROR: {error_msg}")
        driver.quit()
        return False, error_msg, details_opened
    finally:
        # Close the browser
        driver.quit()
        print("Browser closed")
        
    return True, "", details_opened

def process_links_from_file(
    input_file: str,
    output_folder: str = "output",
    retries: int = 3,
    delay: int = 0,
    print_summary: bool = False,
    selected_indices: Optional[List[int]] = None # Add selected_indices parameter
):
    """
    Process multiple links from a file, one link per line.
    Save outputs with sequential numbering in the specified output folder.
    Optionally processes only selected links based on their 1-based index.

    Args:
        input_file (str): Path to the file containing links (one per line)
        output_folder (str): Folder to save outputs (will be created if doesn't exist)
        retries (int): Number of retry attempts per link
        delay (int): Optional delay before starting (seconds)
        print_summary (bool): Whether to print and save report summary at the end
        selected_indices (Optional[List[int]]): List of 1-based link indices to process.
                                                 If None or empty, process all links.
    """
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")

    # Optional initial delay
    if delay > 0:
        print(f"Waiting {delay} seconds before starting...")
        time.sleep(delay)

    # Read links from file
    try:
        with open(input_file, 'r') as f:
            links = [line.strip() for line in f if line.strip()]

        print(f"Found {len(links)} links in {input_file}")
        if not links:
            print("Input file is empty. No links to process.")
            return

        processed_count = 0
        # Process each link
        for i, url in enumerate(links, 1):
            # --- Selection Check ---
            if selected_indices and i not in selected_indices:
                # print(f"Skipping link {i} (not in selection {selected_indices})") # Optional verbose logging
                continue # Skip this link if selection is active and index doesn't match
            # --- End Selection Check ---

            processed_count += 1
            product_id = f"link{i}"
            # report.start_product(product_id) # Moved start_product call below, after check

            print(f"\nProcessing {product_id} (Link #{i}): {url}")
            report.start_product(product_id) # Start reporting *after* selection check

            # Define output filenames for this link
            output_png = os.path.join(output_folder, f"{product_id}.png")

            # Retry logic for each link
            success = False
            last_error = ""
            details_opened = False

            for attempt in range(retries):
                try:
                    print(f"Attempt {attempt+1} of {retries}")
                    success, error_msg, details_opened = take_product_screenshot(url, output_png)
                    last_error = error_msg
                    if success:
                        break # Exit retry loop on success
                except Exception as e:
                    last_error = f"Attempt {attempt+1} failed with error: {str(e)}"
                    print(last_error)
                    # Clean up potentially corrupted files from failed attempt
                    if os.path.exists(output_png):
                        try:
                            os.remove(output_png)
                            print(f"  Removed potentially incomplete file: {output_png}")
                        except OSError as rm_err:
                             print(f"  Warning: Could not remove incomplete file {output_png}: {rm_err}")
                    txt_file = output_png.replace('.png', '.txt')
                    if os.path.exists(txt_file):
                         try:
                            os.remove(txt_file)
                            print(f"  Removed potentially incomplete file: {txt_file}")
                         except OSError as rm_err:
                             print(f"  Warning: Could not remove incomplete file {txt_file}: {rm_err}")

                    if attempt < retries - 1:
                        wait_time = 10 + (random.random() * 15) # 10-25 second wait between retries
                        print(f"Waiting {wait_time:.1f} seconds before next attempt...")
                        time.sleep(wait_time)
                # No explicit else needed here, loop continues or finishes

            # Log final status for this link
            if success:
                print(f"Successfully processed {product_id}: {url}")
                if not details_opened:
                    report.pass_product(product_id, "missing Product Details")
                else:
                    report.pass_product(product_id)
            else:
                print(f"Failed to process {product_id} after {retries} attempts: {url}")
                report.fail_product(product_id, f"All {retries} attempts failed. Last error: {last_error}")

            # Wait between links (only if there are more links *to process*)
            # Check if this is the last *selected* link or the last overall link
            remaining_links_to_process = False
            if selected_indices:
                # Check if there are higher indices in the selection
                if any(sel_idx > i for sel_idx in selected_indices):
                    remaining_links_to_process = True
            elif i < len(links): # If not selecting, check if it's the last link overall
                 remaining_links_to_process = True

            if remaining_links_to_process:
                wait_time = 5 + (random.random() * 10) # 5-15 second wait between links
                print(f"\nWaiting {wait_time:.1f} seconds before next link...")
                time.sleep(wait_time)

        if processed_count == 0 and selected_indices:
             print(f"\nWarning: No links matched the selection criteria: {selected_indices}")

    except FileNotFoundError:
         print(f"Error: Input file '{input_file}' not found.")
         report.fail_product("File Loading", f"Input file '{input_file}' not found.") # Log failure
    except Exception as e:
        print(f"Error processing links file '{input_file}': {e}")
        report.fail_product("File Processing", f"Error processing links file '{input_file}': {e}") # Log failure

    # Print the report summary only if requested (usually handled by main.py now)
    if print_summary:
        report.print_summary()
        report.save_report(output_folder)