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

    # List all frames and their content
    print(f'Total frames: {len(page.frames)}')
    for i, frame in enumerate(page.frames):
        print(f'\nFrame {i}: {frame.url[:70]}...')
        # Get body HTML length
        html_len = frame.evaluate('document.body.innerHTML.length')
        print(f'  Body length: {html_len}')
        # Count divs with class containing 'tile'
        count = frame.evaluate("document.querySelectorAll('[class*=\\\"tile\\\"]').length")
        print(f'  Tile elements: {count}')

    browser.close()
