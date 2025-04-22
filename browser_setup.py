import undetected_chromedriver as uc
from selenium import webdriver

def setup_browser():
    """
    Configure and initialize a browser with anti-detection measures.
    
    Returns:
        webdriver: Configured undetected Chrome webdriver
    """
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
    
    # Initialize undetected ChromeDriver
    return uc.Chrome(options=options)

def handle_cookie_popup(driver):
    """
    Attempt to close the cookie consent popup if present.
    
    Args:
        driver: The webdriver instance
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import random
    import time
    
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