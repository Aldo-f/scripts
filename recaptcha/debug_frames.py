from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.google.com/recaptcha/api2/demo')
    page.wait_for_timeout(3000)
    
    # Find and click reCAPTCHA
    anchor_frame = None
    for frame in page.frames:
        if 'anchor' in frame.url:
            anchor_frame = frame
            break
    
    if anchor_frame:
        print('Clicking checkbox...')
        anchor_frame.locator('.recaptcha-checkbox-border').click()
        page.wait_for_timeout(5000)
        
        # Wait for bframe to appear
        print('Waiting for bframe...')
        page.wait_for_timeout(3000)
        
        # Find bframe
        bframe = None
        for frame in page.frames:
            print(f'  Frame: {frame.url[:70]}')
            if 'bframe' in frame.url:
                bframe = frame
        
        if bframe:
            print(f'\nFound bframe!')
            
            # Try different selectors
            selectors = [
                'table tr td',
                'div[class*="tile"]',
                '.rc-image-tile-2',
                '.rc-imageselect-tile',
            ]
            
            for sel in selectors:
                try:
                    count = bframe.locator(sel).count(timeout=5000)
                    print(f'  {sel}: {count}')
                except Exception as e:
                    print(f'  {sel}: ERROR - {str(e)[:50]}')
    
    browser.close()
