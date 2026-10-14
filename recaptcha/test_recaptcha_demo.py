#!/usr/bin/env python3
"""
reCAPTCHA demo test - solves Google reCAPTCHA v2 demo and shows success.
Saves screenshots at each step for proof.
"""

import os
import sys
import time
import argparse
from datetime import datetime
from camoufox import Camoufox
from faster_whisper import WhisperModel

screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)


def save_screenshot(page, name):
    ts = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    filepath = os.path.join(screenshots_dir, f"{ts}_recaptcha_demo_{name}.png")
    page.screenshot(path=filepath, full_page=True)
    print(f"✓ Screenshot: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://www.google.com/recaptcha/api2/demo")
    args = parser.parse_args()

    print(f"=== reCAPTCHA Demo Test ===")
    print(f"URL: {args.url}")

    # Load Whisper model
    print("Loading Whisper model...")
    whisper_model = WhisperModel("tiny", device="cpu", compute_type="float32")

    # Start Camoufox
    print("Starting Camoufox...")
    with Camoufox(headless="virtual", virtual_display="auto") as browser:
        context = browser.new_context(locale="en-US")
        page = context.new_page()

        # Navigate
        print(f"Navigating to {args.url}...")
        page.goto(args.url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        save_screenshot(page, "01_loaded")

        # Find reCAPTCHA
        print("Looking for reCAPTCHA...")
        anchor_frame = None
        for frame in page.frames:
            if "recaptcha/api2/anchor" in frame.url:
                anchor_frame = frame
                break

        if not anchor_frame:
            print("No reCAPTCHA found on page!")
            save_screenshot(page, "no_recaptcha")
            return

        print(f"Found reCAPTCHA: {anchor_frame.url}")

        # Click checkbox
        print("Clicking reCAPTCHA checkbox...")
        anchor_frame.locator(".recaptcha-checkbox-border").click()
        page.wait_for_timeout(5000)
        save_screenshot(page, "02_checkbox_clicked")

        # Check if solved automatically
        if anchor_frame.locator(".recaptcha-checkbox-checked").count() > 0:
            print("✓ reCAPTCHA solved (automatic check!)")
            save_screenshot(page, "03_solved_auto")
        else:
            # Try audio challenge
            print("Trying audio challenge...")
            try:
                audio_btn = anchor_frame.locator("#recaptcha-audio-button")
                if audio_btn.count() > 0 and audio_btn.is_visible():
                    audio_btn.click()
                    page.wait_for_timeout(5000)
                    save_screenshot(page, "04_audio_started")

                    # Download audio
                    audio_src = anchor_frame.locator("audio#audio-source").get_attribute("src")
                    if audio_src:
                        import requests
                        mp3_path = f"/tmp/captcha_audio_{int(time.time())}.mp3"
                        resp = requests.get(audio_src, timeout=30)
                        with open(mp3_path, "wb") as f:
                            f.write(resp.content)
                        print(f"Downloaded audio: {mp3_path}")

                        # Transcribe
                        wav_path = f"/tmp/captcha_audio_{int(time.time())}.wav"
                        import subprocess
                        subprocess.run([
                            "ffmpeg", "-i", mp3_path,
                            "-f", "wav", "-acodec", "pcm_s16le",
                            "-ar", "16000", "-ac", "1",
                            wav_path, "-y"
                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        print("Transcribing...")
                        segments, info = whisper_model.transcribe(wav_path, language="en")
                        transcription = " ".join([seg.text for seg in segments]).strip()
                        print(f"✓ Transcription: '{transcription}'")

                        # Fill answer
                        page.evaluate("""(text) => {
                            const ta = document.querySelector('#audio-response');
                            if (ta) ta.value = text;
                        }""", transcription)
                        page.wait_for_timeout(1000)
                        save_screenshot(page, "05_audio_answered")

                        # Verify
                        if anchor_frame.locator(".recaptcha-checkbox-checked").count() > 0:
                            print("✓ reCAPTCHA solved via audio!")
                            save_screenshot(page, "06_audio_solved")
                        else:
                            print("⚠ Audio challenge not solved")
                            save_screenshot(page, "07_audio_failed")
                else:
                    print("No audio button found")
            except Exception as e:
                print(f"Audio challenge failed: {e}")

        # Try submitting
        print("Submitting form...")
        try:
            submit_btn = page.locator("text=Submit").first
            if submit_btn.is_visible():
                submit_btn.click()
                page.wait_for_timeout(5000)
                save_screenshot(page, "08_submitted")
        except Exception as e:
            print(f"Submit failed: {e}")
            save_screenshot(page, "09_submit_failed")

    print("\n=== Test Complete ===")
    print(f"Check screenshots in: {screenshots_dir}")


if __name__ == "__main__":
    main()
