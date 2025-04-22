import time
import random
from selenium.webdriver.common.by import By

def find_product_details_button(driver):
    """
    Scroll the page to find the Product Details button or tab.
    
    Args:
        driver: The webdriver instance
        
    Returns:
        tuple: (found_button, button_element) - Whether a button was found and the button element
    """
    # Get the total height of the page
    total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
    
    # Scroll down in smaller increments to locate the Product Details button
    found_details_button = False
    details_button = None
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
        
    return found_details_button, details_button, total_height

def click_details_button(driver, found_button, button_element, total_height):
    """
    Attempt to click the product details button or find alternative ways to open details.
    
    Args:
        driver: The webdriver instance
        found_button: Whether a button was found
        button_element: The button element to click
        total_height: The total height of the page
    """
    try:
        if found_button:
            # Log what we found to help with debugging
            print(f"Found button with text: '{button_element.text}' and tag: {button_element.tag_name}")
            
            # Scroll to make it visible - scroll to a position slightly above the button
            offset = 100  # Scroll to 100px above the element
            element_y = driver.execute_script("return arguments[0].getBoundingClientRect().top + window.pageYOffset;", button_element)
            scroll_to_y = max(0, element_y - offset)
            driver.execute_script(f"window.scrollTo(0, {scroll_to_y});")
            print(f"Scrolled to position {scroll_to_y} to view button")
            time.sleep(2)  # Wait for the scroll
            
            # Attempt to click using JavaScript for reliability
            driver.execute_script("arguments[0].click();", button_element)
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
                try_javascript_details_search(driver)
    except Exception as e:
        print(f"Could not click Product Details tab: {e}")
        print("Continuing to take screenshot anyway...")

def try_javascript_details_search(driver):
    """
    Last resort attempt to find details section using JavaScript.
    
    Args:
        driver: The webdriver instance
    """
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