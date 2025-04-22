import os
import time
import random
from browser_setup import setup_browser, handle_cookie_popup
from details_finder import find_product_details_button, click_details_button
from screenshot_manager import take_full_page_screenshot, extract_page_text
from image_utils import crop_screenshot
from reporting_utils import report

def take_product_screenshot(url, output_filename="product_details.png"):
    """
    Navigate to a Home Depot product page, expand the product details tab,
    and take a full-page screenshot.
    
    Args:
        url (str): The Home Depot product URL
        output_filename (str): Filename to save the screenshot
        
    Returns:
        tuple: (success, error_message)
    """
    print(f"Navigating to: {url}")
    
    # Initialize browser
    try:
        driver = setup_browser()
    except Exception as e:
        error_msg = f"Failed to initialize browser: {str(e)}"
        print(f"ERROR: {error_msg}")
        return False, error_msg
    
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
        
        # Take a full page screenshot
        screenshot_success = take_full_page_screenshot(driver, output_filename)
        if not screenshot_success:
            print("WARNING: Screenshot may not be complete")
        
    except Exception as e:
        error_msg = f"An error occurred during page processing: {str(e)}"
        print(f"ERROR: {error_msg}")
        driver.quit()
        return False, error_msg
    
    try:
        # Extract text before closing the browser
        text_success = extract_page_text(driver, output_filename)
        if not text_success:
            print("WARNING: Text extraction may not be complete")
        
        # Crop the screenshot to remove bottom 1/3
        crop_success = crop_screenshot(output_filename)
        if not crop_success:
            print("WARNING: Screenshot cropping may not be complete")
        
    except Exception as e:
        error_msg = f"Error in post-processing: {str(e)}"
        print(f"ERROR: {error_msg}")
        driver.quit()
        return False, error_msg
    finally:
        # Close the browser
        driver.quit()
        print("Browser closed")
        
    return True, ""

def process_links_from_file(input_file, output_folder="output", retries=3, delay=0):
    """
    Process multiple links from a file, one link per line.
    Save outputs with sequential numbering in the specified output folder.
    
    Args:
        input_file (str): Path to the file containing links (one per line)
        output_folder (str): Folder to save outputs (will be created if doesn't exist)
        retries (int): Number of retry attempts per link
        delay (int): Optional delay before starting (seconds)
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
        
        # Process each link
        for i, url in enumerate(links, 1):
            product_id = f"link{i}"
            report.start_product(product_id)
            
            print(f"\nProcessing {product_id}: {url}")
            
            # Define output filenames for this link
            output_png = os.path.join(output_folder, f"{product_id}.png")
            
            # Retry logic for each link
            success = False
            last_error = ""
            
            for attempt in range(retries):
                try:
                    print(f"Attempt {attempt+1} of {retries}")
                    success, error_msg = take_product_screenshot(url, output_png)
                    last_error = error_msg
                    if success:
                        break
                except Exception as e:
                    last_error = f"Attempt {attempt+1} failed with error: {str(e)}"
                    print(last_error)
                    if attempt < retries - 1:
                        wait_time = 10 + (random.random() * 15)  # 10-25 second wait between retries
                        print(f"Waiting {wait_time:.1f} seconds before next attempt...")
                        time.sleep(wait_time)
                    else:
                        print("All attempts failed for this link.")
            
            if success:
                print(f"Successfully processed {product_id}: {url}")
                report.pass_product(product_id)
            else:
                print(f"Failed to process {product_id} after all attempts: {url}")
                report.fail_product(product_id, last_error)
                
            # Wait between links to avoid overloading the server
            if i < len(links):
                wait_time = 5 + (random.random() * 10)  # 5-15 second wait between links
                print(f"Waiting {wait_time:.1f} seconds before next link...")
                time.sleep(wait_time)
                
    except Exception as e:
        print(f"Error processing links: {e}")
        
    # Print the report summary
    report.print_summary()
    
    # Save the report to a file
    report.save_report(output_folder)