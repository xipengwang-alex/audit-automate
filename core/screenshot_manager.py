import time
import base64
from selenium.webdriver.common.by import By

def take_full_page_screenshot(driver, output_filename):
    """
    Take a full page screenshot using multiple methods, with fallbacks.
    
    Args:
        driver: The webdriver instance
        output_filename: The filename to save the screenshot
        
    Returns:
        bool: Whether the screenshot was successful
    """
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
        with open(output_filename, 'wb') as f:
            f.write(base64.b64decode(screenshot_data['data']))
        
        print(f"CDP screenshot saved as: {output_filename}")
        return True
        
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
            return True
            
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
                return True
            except Exception as e3:
                print(f"All screenshot methods failed. Last error: {e3}")
                print("Saving basic screenshot as fallback")
                driver.save_screenshot(output_filename)
                print(f"Basic screenshot saved as: {output_filename}")
                return True
    
    return False

def extract_page_text(driver, output_filename):
    """
    Extract text content from the page and save to a text file.
    
    Args:
        driver: The webdriver instance
        output_filename: The png filename to derive the text filename from
    """
    try:
        print("Extracting page text as final step...")
        
        # Use the simplest possible method to get text
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        
        # Save to file
        text_filename = output_filename.replace('.png', '.txt')
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write(page_text)
        
        print(f"Text saved to: {text_filename}")
        return True
    except Exception as text_err:
        print(f"Error saving text: {text_err}")
        return False