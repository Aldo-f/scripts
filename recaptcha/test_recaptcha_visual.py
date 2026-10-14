#!/usr/bin/env python3
import os, sys, time, argparse
from datetime import datetime
from camoufox import Camoufox

screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
os.makedirs(screenshots_dir, exist_ok=True)

def save_screenshot(page, name):
    ts = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    filepath = os.path.join(screenshots_dir, f'{ts}_{name}.png')
    page.screenshot(path=filepath, full_page=True)
    print(f'  Screenshot: {filepath}')
    return filepath

def solve_recaptcha_demo(url='https://www.google.com/recaptcha/api2/demo'):
    print(f'=== reCAPTCHA Demo Test ===')
    print(f'URL: {url}')

    with Camoufox(headless='virtual', virtual_display='auto') as browser:
        context = browser.new_context(locale='en-US')
        page = context.new_page()

        print('Navigating...')
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)
        save_screenshot(page, '01_loaded')

        # Find anchor frame (bframe not yet present)
        anchor_frame = None
        for frame in page.frames:
            if 'anchor' in frame.url:
                anchor_frame = frame
                break

        if not anchor_frame:
            print('No reCAPTCHA found!')
            return False

        # Click checkbox
        print('Clicking checkbox...')
        anchor_frame.locator('.recaptcha-checkbox-border').click()
        page.wait_for_timeout(5000)
        save_screenshot(page, '02_checkbox')

        # Check auto-solved
        if anchor_frame.locator('.recaptcha-checkbox-checked').count() > 0:
            print('Auto-solved!')
            save_screenshot(page, '03_auto_solved')
            return True

        # Wait for bframe to appear
        print('Waiting for bframe...')
        page.wait_for_timeout(3000)

        # Find bframe NOW (after click)
        bframe = None
        for frame in page.frames:
            if 'bframe' in frame.url:
                bframe = frame
                break

        if not bframe:
            print('No bframe found!')
            save_screenshot(page, '04_no_bframe')
            return False

        print(f'Bframe found: {bframe.url[:70]}')

        # Get instruction
        instruction = ''
        try:
            instruction = bframe.locator('.rc-imageselect-instructions').text_content()
            print(f'Instruction: {instruction}')
        except Exception as e:
            print(f'Could not get instruction: {e}')

        if not instruction:
            instruction = 'crosswalk'

        # Find tiles in bframe
        try:
            tile_count = bframe.locator('table tr td').count()
            print(f'Table cells: {tile_count}')
        except Exception as e:
            print(f'Cell count error: {e}')
            tile_count = 0

        if tile_count == 0:
            print('No tiles found!')
            save_screenshot(page, '04_no_tiles')
            return False

        # Determine which tiles to select based on instruction
        if 'bicycle' in instruction.lower():
            selections = [3, 6, 8]
        else:
            selections = [0, 1, 5]

        print(f'Selecting tiles: {selections}')
        for i in selections:
            if i < tile_count:
                try:
                    tile = bframe.locator('table tr td').nth(i)
                    tile.click()
                    print(f'  Selected tile {i}')
                except Exception as e:
                    print(f'  Failed tile {i}: {e}')

        save_screenshot(page, '05_selected')

        # Click VERIFY
        print('Clicking VERIFY...')
        verify_btn = anchor_frame.locator('button#recaptcha-verify-button')
        if verify_btn.is_visible(timeout=3000):
            verify_btn.click()
            page.wait_for_timeout(3000)
            save_screenshot(page, '06_verified')

            # Check result
            if anchor_frame.locator('.recaptcha-checkbox-checked').count() > 0:
                print('SUCCESS!')
                return True

        save_screenshot(page, '07_final')
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='https://www.google.com/recaptcha/api2/demo')
    args = parser.parse_args()

    success = solve_recaptcha_demo(args.url)

    print(f'\n=== Result ===')
    if success:
        print('SUCCESS - reCAPTCHA solved!')
        sys.exit(0)
    else:
        print('FAILED - check screenshots')
        print(f'Screenshots: {screenshots_dir}')
        sys.exit(1)

if __name__ == '__main__':
    main()
