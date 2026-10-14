#!/usr/bin/env python3
"""
Solve reCAPTCHA v2 using Camoufox + Buster + Whisper.
Uses proper frame handling for audio challenges.
"""
import os
import sys
import time
import argparse
import subprocess
from datetime import datetime

screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)


def save_screenshot(page, name):
    ts = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    filepath = os.path.join(screenshots_dir, f"{ts}_{name}.png")
    page.screenshot(path=filepath, full_page=True)
    print(f"  Screenshot: {filepath}")
    return filepath


def transcribe_audio(mp3_path, whisper_model):
    """Transcribe audio using Whisper."""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(whisper_model, device="cpu", compute_type="float32")
        segments, info = model.transcribe(mp3_path, beam_size=5)
        transcription = " ".join([seg.text for seg in segments]).strip()
        return transcription
    except Exception as e:
        print(f"  Whisper error: {e}")
        return None


def solve_recaptcha(url, timeout=180000):
    """Solve reCAPTCHA for the given URL."""
    from camoufox import Camoufox
    from playwright.sync_api import sync_playwright
    import requests

    print(f"=== Solving reCAPTCHA for: {url} ===")

    # Find buster addon
    buster_addon = os.path.expanduser("~/dev/06-apps-urbanfix/tools/buster/buster_extension_firefox")
    if not os.path.exists(buster_addon):
        buster_addon = os.path.expanduser("~/buster_ext")

    print(f"Buster addon: {buster_addon}")
    print(f"Exists: {os.path.exists(buster_addon)}")

    # Load Whisper model
    print("Loading Whisper model (tiny)...")
    whisper_model = "tiny"

    print("Starting Camoufox (Buster + Whisper)...")

    with Camoufox(headless="virtual", virtual_display="auto", addons=[buster_addon] if buster_addon else []) as browser:
        context = browser.new_context(locale="en-US")
        page = context.new_page()

        # Navigate
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        save_screenshot(page, "01_target_page")

        # Find reCAPTCHA frames
        anchor_frame = None
        bframe = None
        for frame in page.frames:
            if "recaptcha/api2/anchor" in frame.url:
                anchor_frame = frame
                print(f"  Found anchor: {frame.url[:60]}")
            elif "recaptcha/api2/bframe" in frame.url:
                bframe = frame
                print(f"  Found bframe: {frame.url[:60]}")

        if not anchor_frame:
            print("No reCAPTCHA found!")
            return False

        # Click checkbox
        print("Clicking 'I'm not a robot'...")
        anchor_frame.locator(".recaptcha-checkbox-border").click()
        page.wait_for_timeout(5000)
        save_screenshot(page, "02_checkbox_clicked")

        # Wait for bframe
        print("Waiting for bframe...")
        page.wait_for_timeout(3000)

        # Find bframe again (may have appeared after click)
        for frame in page.frames:
            if "recaptcha/api2/bframe" in frame.url:
                bframe = frame
                print(f"  Found bframe: {frame.url[:60]}")
                break

        # Check if auto-solved
        if anchor_frame.locator(".recaptcha-checkbox-checked").count() > 0:
            print("✓ reCAPTCHA solved automatically!")
            save_screenshot(page, "03_auto_solved")
            return True

        # Look for audio challenge in bframe or anchor
        target_frame = bframe or anchor_frame
        print(f"Using frame: {target_frame.url[:60]}")

        # Look for audio button
        audio_btn = target_frame.locator("#recaptcha-audio-button")
        if audio_btn.count() > 0 and audio_btn.is_visible():
            print("Found audio button, clicking...")
            audio_btn.click()
            page.wait_for_timeout(3000)
            save_screenshot(page, "04_audio_started")

            # Wait for audio player
            page.wait_for_timeout(2000)
            
            # Click PLAY button
            play_btn = target_frame.locator("button:has-text('PLAY')")
            if play_btn.count() > 0:
                print("Clicking PLAY...")
                play_btn.click()
                page.wait_for_timeout(4000)
                save_screenshot(page, "05_audio_playing")

            # Get audio source using evaluate
            print("Getting audio source...")
            audio_src = target_frame.evaluate("""
                () => {
                    const audio = document.querySelector('audio');
                    return audio ? audio.src : null;
                }
            """)
            
            if audio_src:
                mp3_path = f"/tmp/captcha_audio_{int(time.time())}.mp3"
                print(f"Downloading audio from: {audio_src[:60]}...")
                resp = requests.get(audio_src, timeout=30)
                resp.raise_for_status()
                with open(mp3_path, "wb") as f:
                    f.write(resp.content)
                print(f"Downloaded to: {mp3_path}")

                # Transcribe
                print("Transcribing with Whisper...")
                transcription = transcribe_audio(mp3_path, whisper_model)
                if transcription:
                    print(f"✓ Transcription: '{transcription}'")

                    # Fill the audio response field
                    print("Filling response field...")
                    target_frame.locator("#audio-response").fill(transcription)
                    page.wait_for_timeout(1000)
                    save_screenshot(page, "06_audio_answered")

                    # Click VERIFY button
                    verify_btn = target_frame.locator("button#recaptcha-verify-button")
                    if verify_btn.count() > 0 and verify_btn.is_visible():
                        print("Clicking VERIFY...")
                        verify_btn.click()
                        page.wait_for_timeout(3000)
                        save_screenshot(page, "07_verified")

                        # Check result
                        if anchor_frame.locator(".recaptcha-checkbox-checked").count() > 0:
                            print("✓ reCAPTCHA solved via audio!")
                            return True
                        else:
                            print("⚠ Verification failed - wrong transcription")
                            save_screenshot(page, "08_failed")
                    else:
                        print("⚠ VERIFY button not found")
                        save_screenshot(page, "09_no_verify")
                else:
                    print("✗ Transcription failed")
            else:
                print("⚠ No audio source found")
        else:
            print("No audio challenge found - checking for visual challenge...")
            save_screenshot(page, "10_visual_challenge")

        save_screenshot(page, "11_final")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--timeout", type=int, default=180000)
    args = parser.parse_args()

    success = solve_recaptcha(args.url, args.timeout)

    if success:
        print("\n=== SUCCESS ===")
        sys.exit(0)
    else:
        print("\n=== FAILED ===")
        print(f"Check screenshots in: {screenshots_dir}")
        sys.exit(1)


if __name__ == "__main__":
    main()
