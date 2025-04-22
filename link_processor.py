import os
import time
import random
from browser_setup import setup_browser, handle_cookie_popup
from details_finder import find_product_details_button, click_details_button
from screenshot_manager import take_full_page_screenshot, extract_page_text
from image_utils import crop_screenshot

def take_product_screenshot(url, output_filename="product_details.png"):
    """
    Navigate to a Home Depot product page, expand the product details tab,
    and take a full-page screenshot.
    
    Args:
        url (str): The Home Depot product URL
        output_filename (str): Filename to save the screenshot
    """
    print(f"Navigating to: {url}")
    
    # Initialize browser
    driver = setup_browser()
    
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
        take_full_page_screenshot(driver, output_filename)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        # Extract text before closing the browser
        extract_page_text(driver, output_filename)
        
        # Crop the screenshot to remove bottom 1/3
        crop_screenshot(output_filename)
        
        # Close the browser
        driver.quit()
        print("Browser closed")
        
    return True

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
            print(f"\n{'='*50}")
            print(f"Processing link {i}/{len(links)}: {url}")
            print(f"{'='*50}\n")
            
            # Define output filenames for this link
            output_png = os.path.join(output_folder, f"link{i}.png")
            
            # Retry logic for each link
            success = False
            for attempt in range(retries):
                try:
                    print(f"Attempt {attempt+1} of {retries}")
                    success = take_product_screenshot(url, output_png)
                    if success:
                        break
                except Exception as e:
                    print(f"Attempt {attempt+1} failed with error: {e}")
                    if attempt < retries - 1:
                        wait_time = 10 + (random.random() * 15)  # 10-25 second wait between retries
                        print(f"Waiting {wait_time:.1f} seconds before next attempt...")
                        time.sleep(wait_time)
                    else:
                        print("All attempts failed for this link.")
            
            if success:
                print(f"Successfully processed link {i}: {url}")
            else:
                print(f"Failed to process link {i} after all attempts: {url}")
                
            # Wait between links to avoid overloading the server
            if i < len(links):
                wait_time = 5 + (random.random() * 10)  # 5-15 second wait between links
                print(f"Waiting {wait_time:.1f} seconds before next link...")
                time.sleep(wait_time)
                
    except Exception as e:
        print(f"Error processing links: {e}")