# core/browser_setup.py (Simplified)
import undetected_chromedriver as uc

def setup_browser():
    """
    Configure and initialize a browser with anti-detection measures.

    Returns:
        webdriver: Configured undetected Chrome webdriver
    """
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument("--headless") # Optional: run headless
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-infobars")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36') # Keep a reasonable UA

    # Consider adding options to disable images or javascript if needed for speed/stability
    # options.add_argument('--blink-settings=imagesEnabled=false')

    try:
        print("Initializing undetected ChromeDriver...")
        # driver = uc.Chrome(options=options, driver_executable_path='/path/to/chromedriver')
        driver = uc.Chrome(options=options) # Let the library detect the version
        print("Browser initialized.")
        return driver
    except Exception as e:
         print(f"Error initializing browser: {e}")
         print("Ensure chromedriver matching your Chrome version is installed and accessible.")
         raise # Re-raise the exception

# handle_cookie_popup function is removed - handled by retailer auditors now.