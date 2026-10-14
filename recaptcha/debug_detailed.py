#!/usr/bin/env python3
import os, sys
from camoufox import Camoufox

print('=== Debug reCAPTCHA ===')

with Camoufox(headless='virtual', virtual_display='auto') as browser:
    context = browser.new_context(locale='en-US')
    page = context.new_page()

    print('Navigating...')
    page.goto('https://www.google.com/recaptcha/api2/demo', wait_until='domcontentloaded')
    page.wait_for_timeout(3000)

    # List all frames
    print(f'\\nTotal frames: {len(page.frames)}')
    for i, frame in enumerate(page.frames):
        print(f'  Frame {i}: {frame.url[:70]}')

    # Find anchor and bframe
    anchor_frame = None
    bframe = None
    for frame in page.frames:
        if 'anchor' in frame.url:
            anchor_frame = frame
            print(f'\\nAnchor frame found: {frame.url[:70]}')
        elif 'bframe' in frame.url:
            bframe = frame
            print(f'Bframe found: {frame.url[:70]}')

    # Click checkbox
    if anchor_frame:
        print('\\nClicking checkbox...')
        anchor_frame.locator('.recaptcha-checkbox-border').click()
        page.wait_for_timeout(5000)

        # List frames again after click
        print(f'\\nFrames after click: {len(page.frames)}')
        for i, frame in enumerate(page.frames):
            print(f'  Frame {i}: {frame.url[:70]}')

        # Find bframe again
        for frame in page.frames:
            if 'bframe' in frame.url:
                bframe = frame
                print(f'\\nBframe now found!')
                break

        if bframe:
            # Try to get instruction
            try:
                instruction = bframe.locator('.rc-imageselect-instructions').text_content()
                print(f'Instruction: {instruction}')
            except Exception as e:
                print(f'Instruction error: {e}')

            # Try to find tiles
            try:
                tile_count = bframe.locator('table tr td').count()
                print(f'Table cells: {tile_count}')
            except Exception as e:
                print(f'Table count error: {e}')

            try:
                tile_count2 = bframe.locator('[class*="tile"]').count()
                print(f'Tile class elements: {tile_count2}')
            except Exception as e:
                print(f'Tile class count error: {e}')

    print('\\nDone!')
    page.screenshot(path='/tmp/debug_screenshot.png', full_page=True)
    print('Screenshot saved to /tmp/debug_screenshot.png')
