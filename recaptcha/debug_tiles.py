from playwright.sync_api import sync_playwright
import os

screenshots_dir = '/tmp/recaptcha_debug'
os.makedirs(screenshots_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)
    page = browser.new_page()
    
    print('Navigating...')
    page.goto('https://www.google.com/recaptcha/api2/demo')
    page.wait_for_timeout(3000)
    
    # Find anchor frame
    anchor_frame = None
    for frame in page.frames:
        if 'anchor' in frame.url:
            anchor_frame = frame
            break
    
    if anchor_frame:
        print('Clicking checkbox...')
        anchor_frame.locator('.recaptcha-checkbox-border').click()
        page.wait_for_timeout(5000)
        
        # Wait for bframe
        print('Waiting for bframe...')
        page.wait_for_timeout(3000)
        
        # Find bframe
        bframe = None
        for frame in page.frames:
            print(f'  Frame: {frame.url[:60]}')
            if 'bframe' in frame.url:
                bframe = frame
                print(f'  Found bframe!')
                break
        
        if bframe:
            # Get instruction
            try:
                instruction = bframe.locator('.rc-imageselect-instructions').text_content()
                print(f'Instruction: {instruction}')
            except Exception as e:
                print(f'Instruction error: {e}')
            
            # Get tile count
            try:
                tile_count = bframe.locator('table tr td').count()
                print(f'Tile count: {tile_count}')
                
                # Capture each tile
                for i in range(min(tile_count, 16)):
                    try:
                        cell = bframe.locator('table tr td').nth(i)
                        if cell.is_visible():
                            cell_path = os.path.join(screenshots_dir, f'tile_{i}.png')
                            cell.screenshot(path=cell_path)
                            print(f'  Captured tile {i}')
                    except Exception as e:
                        print(f'  Tile {i} error: {e}')
            except Exception as e:
                print(f'Tile count error: {e}')
    
    browser.close()
