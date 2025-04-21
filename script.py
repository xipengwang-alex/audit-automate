import time
import random
import argparse
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def take_product_screenshot(url, output_filename="product_details.png"):
    """
    Navigate to a Home Depot product page, expand the product details tab,
    and take a full-page screenshot.
    
    Args:
        url (str): The Home Depot product URL
        output_filename (str): Filename to save the screenshot
    """
    print(f"Navigating to: {url}")
    
    # Set up Chrome options with anti-detection measures
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")  # Start maximized
    
    # Additional anti-detection settings
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-infobars")
    
    # Set a common user agent
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
    
    # Add random delays between actions to appear more human-like
    # (We'll implement random delays during interactions)
    
    # Initialize undetected ChromeDriver
    driver = uc.Chrome(options=options)
    
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
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
            )
            # Move mouse to button before clicking (more human-like)
            actions = webdriver.ActionChains(driver)
            actions.move_to_element(cookie_button).pause(random.random()).click().perform()
            print("Closed cookie consent popup")
            time.sleep(random.random() * 2)  # 0-2 second delay after closing
        except:
            print("No cookie popup detected or timed out waiting")
        
        # First, scroll down the page to find the Product Details area
        print("Scrolling page slowly to locate Product Details section...")
        
        # Get the total height of the page
        total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
        
        # Scroll down in smaller increments to locate the Product Details button
        found_details_button = False
        current_position = 0
        max_scroll_attempts = 20  # More attempts with smaller increments
        scroll_attempts = 0
        
        # More precise selectors for the Product Details button
        detail_selectors = [
            "//button[text()='Product Details']",  # Exact text match
            "//button[normalize-space(text())='Product Details']",  # Normalized text
            "//button[contains(@class, 'detail') and not(contains(@class, 'list'))]",  # Has detail in class but not list
            "//button[@aria-label='Product Details']",  # Exact aria-label
            "//span[text()='Product Details']/parent::button",  # Text in child span
            "//span[contains(text(), 'Specifications')]/parent::button",  # Sometimes labeled as Specifications
            "//button[contains(@data-id, 'detail')]",  # Detail in data-id
            "//a[text()='View More Details']",  # Link with exact text
            "//div[contains(@class, 'accordion-title') and contains(text(), 'Details')]",  # Accordion style
            "//div[contains(text(), 'Product Details')]",  # Div with text
            "//p[contains(text(), 'Product Details')]",  # Paragraph with text
            "//a[contains(text(), 'Product Details')]"  # Link with text
        ]
        
        # Use smaller scroll increments (300px instead of 800px)
        scroll_increment = 300
        
        while not found_details_button and scroll_attempts < max_scroll_attempts and current_position < total_height:
            # Look for Detail elements with exact matching to avoid Add to List
            for selector in detail_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        # Check if it's visible
                        if element.is_displayed():
                            # Double check it's not an "Add to" button
                            element_text = element.text.lower() if element.text else ""
                            if 'add to' not in element_text and 'cart' not in element_text and 'list' not in element_text:
                                # Found the Product Details button
                                details_button = element
                                found_details_button = True
                                print(f"Found Product Details button with text: '{element.text}'")
                                break
                except Exception as e:
                    continue
                    
            if found_details_button:
                break
                
            # Scroll down more with smaller increment
            scroll_attempts += 1
            current_position += scroll_increment
            
            # Don't scroll past the end of the page
            if current_position > total_height:
                current_position = total_height
            
            # Scroll to new position
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            print(f"Scrolled to position {current_position}/{total_height} (attempt {scroll_attempts})")
            
            # Wait three seconds between scrolls for elements to load
            time.sleep(3)
            
        # Try to click the Product Details tab
        print("Attempting to click Product Details tab...")
        try:
            if found_details_button:
                # Log what we found to help with debugging
                print(f"Found button with text: '{details_button.text}' and tag: {details_button.tag_name}")
                
                # Scroll to make it visible - scroll to a position slightly above the button
                offset = 100  # Scroll to 100px above the element
                element_y = driver.execute_script("return arguments[0].getBoundingClientRect().top + window.pageYOffset;", details_button)
                scroll_to_y = max(0, element_y - offset)
                driver.execute_script(f"window.scrollTo(0, {scroll_to_y});")
                print(f"Scrolled to position {scroll_to_y} to view button")
                time.sleep(2)  # Wait for the scroll
                
                # Attempt to click using JavaScript for reliability
                driver.execute_script("arguments[0].click();", details_button)
                print("Clicked on Product Details tab using JavaScript")
                
                # Wait for details to expand
                time.sleep(3)
            else:
                print("Could not find Product Details button by scrolling")
                
                # Try one more attempt with a specific selector for the "View More Details" link
                print("Looking for 'View More Details' link...")
                try:
                    # First scroll back to the middle of the page where this link often is
                    mid_page = total_height / 2
                    driver.execute_script(f"window.scrollTo(0, {mid_page});")
                    time.sleep(2)
                    
                    # Search specifically for the link
                    view_more_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'View More Details')]")
                    for link in view_more_links:
                        if link.is_displayed():
                            print("Found 'View More Details' link")
                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", link)
                            time.sleep(2)
                            driver.execute_script("arguments[0].click();", link)
                            print("Clicked 'View More Details' link")
                            time.sleep(3)
                            break
                    else:
                        print("No visible 'View More Details' link found")
                except Exception as e:
                    print(f"Error finding 'View More Details' link: {e}")
                    
                    # Last resort: search for any element that seems like "details"
                    print("Searching for any details element...")
                    try:
                        # Check for the heading that's often above the details
                        driver.execute_script("""
                            // This function looks specifically for product details sections
                            function findProductDetailsElement() {
                                // Check for common detail patterns
                                const patterns = [
                                    {tag: 'h2', text: 'Product Details'},
                                    {tag: 'h3', text: 'Product Details'},
                                    {tag: 'h4', text: 'Product Details'},
                                    {tag: 'h2', text: 'Specifications'},
                                    {tag: 'h3', text: 'Specifications'},
                                    {tag: 'button', text: 'Details'},
                                    {tag: 'a', text: 'More Details'},
                                    {tag: 'span', text: 'Product Details'},
                                    {tag: 'div', class: 'specifications'}
                                ];
                                
                                for (const pattern of patterns) {
                                    let elements;
                                    if (pattern.class) {
                                        elements = document.getElementsByClassName(pattern.class);
                                    } else {
                                        elements = document.getElementsByTagName(pattern.tag);
                                    }
                                    
                                    for (const el of elements) {
                                        if (!pattern.class && pattern.text && el.textContent.includes(pattern.text)) {
                                            console.log('Found element by text match:', el);
                                            return el;
                                        } else if (pattern.class) {
                                            console.log('Found element by class:', el);
                                            return el;
                                        }
                                    }
                                }
                                
                                // Find "View More Details" or similar 
                                for (const a of document.querySelectorAll('a')) {
                                    if (a.textContent.includes('Details') || 
                                        a.textContent.includes('Specifications') ||
                                        a.getAttribute('data-automation-id') === 'specifications' ||
                                        a.getAttribute('data-automation-id') === 'details') {
                                        console.log('Found anchor with details:', a);
                                        return a;
                                    }
                                }
                                
                                return null;
                            }
                            
                            const el = findProductDetailsElement();
                            if (el) {
                                el.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    try {
                                        el.click();
                                    } catch(e) {
                                        // If clicking fails, try to find a clickable parent
                                        let parent = el.parentElement;
                                        for (let i = 0; i < 3 && parent; i++) {
                                            try {
                                                parent.click();
                                                console.log('Clicked parent:', parent);
                                                break;
                                            } catch(e) {
                                                parent = parent.parentElement;
                                            }
                                        }
                                    }
                                }, 1000);
                                return true;
                            }
                            return false;
                        """)
                        time.sleep(3)
                    except Exception as e:
                        print(f"JavaScript search failed: {e}")
                        print("Continuing to take screenshot anyway...")
        except Exception as e:
            print(f"Could not click Product Details tab: {e}")
            print("Continuing to take screenshot anyway...")
        
        # Take a full page screenshot using a better approach
        print("Taking full page screenshot...")
        
        try:
            # Using CDP (Chrome DevTools Protocol) to capture full page
            # This is the most reliable method for modern websites
            print("Using CDP method for full page screenshot")
            
            # Get page dimensions with CDP
            page_dimensions = driver.execute_cdp_cmd('Page.getLayoutMetrics', {})
            width = int(page_dimensions['contentSize']['width'])
            height = int(page_dimensions['contentSize']['height'])
            
            # Set window size
            driver.set_window_size(width, height)
            
            # Capture screenshot of the entire content
            screenshot_config = {
                'format': 'png',
                'fromSurface': True,
                'captureBeyondViewport': True,
                'clip': {
                    'x': 0,
                    'y': 0,
                    'width': width,
                    'height': height,
                    'scale': 1
                }
            }
            
            # Take the screenshot
            screenshot_data = driver.execute_cdp_cmd('Page.captureScreenshot', screenshot_config)
            
            # Save the image
            import base64
            with open(output_filename, 'wb') as f:
                f.write(base64.b64decode(screenshot_data['data']))
            
            print(f"CDP screenshot saved as: {output_filename}")
            
        except Exception as e:
            print(f"CDP screenshot method failed: {e}")
            print("Trying alternative method with scrolling capture...")
            
            try:
                # Alternative method: Selenium Firefox approach with JS
                print("Using Firefox-style full page screenshot via JS")
                
                # Get the entire page height
                total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);")
                total_width = driver.execute_script("return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth);")
                
                # Set viewport size
                driver.set_window_size(total_width, total_height)
                
                # Wait for resize
                time.sleep(2)
                
                # Take screenshot
                driver.save_screenshot(output_filename)
                print(f"Full page screenshot saved as: {output_filename}")
                
            except Exception as e2:
                print(f"Alternative method failed: {e2}")
                print("Trying final method with stitching...")
                
                try:
                    # Final fallback: stitch multiple screenshots
                    from PIL import Image
                    import io
                    
                    # Get viewport size
                    viewport_height = driver.execute_script("return window.innerHeight")
                    viewport_width = driver.execute_script("return window.innerWidth")
                    
                    # Get total document size
                    total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);")
                    total_width = driver.execute_script("return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth);")
                    
                    # Create a new blank image
                    stitched_image = Image.new('RGB', (viewport_width, total_height))
                    
                    # Loop through and take screenshots at different scroll positions
                    offset = 0
                    while offset < total_height:
                        # Scroll to position
                        driver.execute_script(f"window.scrollTo(0, {offset});")
                        time.sleep(0.5)  # Allow time for page to render
                        
                        # Take screenshot of current viewport
                        screenshot = driver.get_screenshot_as_png()
                        
                        # Convert to PIL image
                        image = Image.open(io.BytesIO(screenshot))
                        
                        # Calculate remaining height
                        if offset + viewport_height > total_height:
                            # Crop the final image portion if it's at the end
                            scroll_height = total_height - offset
                            cropped_image = image.crop((0, 0, viewport_width, scroll_height))
                            stitched_image.paste(cropped_image, (0, offset))
                        else:
                            # Paste the full viewport
                            stitched_image.paste(image, (0, offset))
                        
                        # Move down one viewport height minus a little overlap
                        overlap = 100  # 100px overlap to handle dynamic content
                        offset += viewport_height - overlap
                    
                    # Save the stitched image
                    stitched_image.save(output_filename)
                    print(f"Stitched screenshot saved as: {output_filename}")
                except Exception as e3:
                    print(f"All screenshot methods failed. Last error: {e3}")
                    print("Saving basic screenshot as fallback")
                    driver.save_screenshot(output_filename)
                    print(f"Basic screenshot saved as: {output_filename}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the browser
        driver.quit()
        print("Browser closed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Take a screenshot of Home Depot product details")
    parser.add_argument("url", help="The Home Depot product URL")
    parser.add_argument("--output", "-o", default="product_details.png", 
                        help="Output filename for the screenshot (default: product_details.png)")
    parser.add_argument("--delay", "-d", type=int, default=0,
                       help="Optional delay in seconds before starting (to allow manual proxy setup)")
    parser.add_argument("--retries", "-r", type=int, default=3,
                       help="Number of attempts to make if initial attempts fail (default: 3)")
    
    args = parser.parse_args()
    
    # Optional initial delay
    if args.delay > 0:
        print(f"Waiting {args.delay} seconds before starting...")
        time.sleep(args.delay)
    
    # Retry logic
    success = False
    for attempt in range(args.retries):
        try:
            print(f"Attempt {attempt+1} of {args.retries}")
            take_product_screenshot(args.url, args.output)
            success = True
            break
        except Exception as e:
            print(f"Attempt {attempt+1} failed with error: {e}")
            if attempt < args.retries - 1:
                wait_time = 10 + (random.random() * 15)  # 10-25 second wait between retries
                print(f"Waiting {wait_time:.1f} seconds before next attempt...")
                time.sleep(wait_time)
            else:
                print("All attempts failed.")
    
    if success:
        print("Screenshot successfully captured!")
    else:
        print("Failed to capture screenshot after all attempts.")