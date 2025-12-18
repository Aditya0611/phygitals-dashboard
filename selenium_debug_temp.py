from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import sys
import os
import time

print("--- SELENIUM DIAGNOSTIC START ---")
try:
    print(f"Python executable: {sys.executable}")
    print(f"CWD: {os.getcwd()}")
    
    print("Configuring options...")
    chrome_options = Options()
    chrome_options.add_argument('--headless=new') 
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--log-level=0') # Verbose
    
    # Try locating chromedriver manually if needed, or rely on PATH
    print("Checking for chromedriver...")
    # Attempt to use webdriver_manager if available, else standard
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print("webdriver_manager found. Installing driver...")
        driver_path = ChromeDriverManager().install()
        print(f"Driver installed at: {driver_path}")
        service = Service(driver_path)
    except ImportError:
        print("webdriver_manager NOT found. Using default service.")
        service = None
    except Exception as e:
        print(f"Error in webdriver_manager: {e}")
        service = None

    print("Initializing WebDriver (this is where it hangs)...")
    start_time = time.time()
    
    if service:
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)
        
    print(f"WebDriver success! Took {time.time() - start_time:.2f}s")
    
    print("Navigating...")
    driver.set_page_load_timeout(10)
    driver.get("https://www.google.com")
    print(f"Title: {driver.title}")
    
    driver.quit()
    print("--- SUCCESS ---")

except Exception as e:
    print(f"\n--- FAILURE ---")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")
    import traceback
    traceback.print_exc()
