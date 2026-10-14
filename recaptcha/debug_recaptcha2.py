from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.google.com/recaptcha/api2/demo')
    page.wait_for_timeout(3000)

    # Find and click reCAPTCHA
    for frame in page.frames:
        if 'anchor' in frame.url:
            frame.locator('.recaptcha-checkbox-border').click()
            page.wait_for_timeout(5000)
            break

    # Find bframe with tiles
    bframe = None
    for frame in page.frames:
        if 'bframe' in frame.url:
            bframe = frame
            break
    
    if bframe:
        print(f'bframe: {bframe.url[:70]}')
        
        # Get all div elements
        divs = bframe.evaluate('''
            () => {
                const divs = document.querySelectorAll('div');
                return Array.from(divs).slice(0, 30).map(d => d.className).join(' | ');
            }
        ''')
        print(f'First 30 div classes: {divs}')
        
        # Try different selectors
        selectors = [
            'div.rc-imageselect-tile',
            'div.rc-image-tile-2', 
            'table tr td',
            '[class*="tile"]',
            'img',
        ]
        
        for sel in selectors:
            try:
                count = bframe.locator(sel).count()
                print(f'  {sel}: {count}')
            except Exception as e:
                print(f'  {sel}: ERROR - {e}')
        
        # Get all table rows
        rows = bframe.locator('table tr').count()
        print(f'\\nTable rows: {rows}')
        for r in range(min(rows, 4)):
            cells = bframe.locator(f'table tr:nth-child({r+1}) td').count()
            print(f'  Row {r+1}: {cells} cells')
    
    browser.close()
