#!/usr/bin/env python3
"""
ReCAPTCHA solver - focuses on the checkbox and takes a screenshot of the result.
Works standalone (no UrbanFix dependencies required).

Usage:
    python3 /home/aldo/dev/scripts/solve_recaptcha_generic.py --url https://www.google.com/recaptcha/api2/demo
"""

import os
import sys
import time
import re
import argparse
import requests
import subprocess
from datetime import datetime
from camoufox import Camoufox
from faster_whisper import WhisperModel

# Screenshots are saved relative to this script's directory
screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)

step_counter = 0
target_url = ""


def sanitize_url(url):
    """Converts a URL into a safe filename segment."""
    # Remove scheme, collapse slashes, dots, colons, question marks, & to underscores
    url = url.replace("https://", "").replace("http://", "").replace("://", "")
    url = url.replace("/", "_").replace(":", "_").replace("?", "_").replace("&", "_")
    url = re.sub(r"__+", "_", url).strip("_")
    return url


def save_screenshot(page, name):
    """Saves a screenshot with timestamp + URL + step name in the filename."""
    global step_counter
    step_counter += 1
    ts = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    url_slug = sanitize_url(target_url) if target_url else "unknown"
    filepath = os.path.join(screenshots_dir, f"{ts}_{url_slug}_{step_counter:02d}_{name}.png")
    page.screenshot(path=filepath, full_page=True)
    print(f"✓ Screenshot saved: {filepath}")
    return filepath


def transcribe_audio(mp3_path, whisper_model):
    """Converts MP3 to WAV and transcribes with Whisper."""
    print(f"Converting MP3 to WAV 16kHz mono: {mp3_path}")
    wav_path = f"/tmp/captcha_audio_{int(time.time())}.wav"
    try:
        subprocess.run(
            [
                "ffmpeg", "-i", mp3_path,
                "-f", "wav",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                wav_path,
                "-y"
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={"LD_LIBRARY_PATH": "/usr/lib/aarch64-linux-gnu"}
        )
        print("Transcribing audio with Whisper...")
        segments, info = whisper_model.transcribe(wav_path, language="en")
        transcription = " ".join([seg.text for seg in segments]).strip()
        print(f"✓ Transcription: '{transcription}'")
        return transcription
    except Exception as e:
        print(f"⚠ Audio conversion failed: {e}")
        return ""


def solve_recaptcha(target_url_param, timeout=120):
    """Solve reCAPTCHA and save a screenshot of the result."""
    global target_url
    target_url = target_url_param
    print(f"=== Solving reCAPTCHA for: {target_url} ===")
    
    # Load Whisper model (tiny)
    print("Loading Whisper model (tiny)...")
    whisper_model = WhisperModel("tiny", device="cpu", compute_type="float32")
    
    # Path to Buster extension
    buster_addon = os.path.expanduser("~/dev/06-apps-urbanfix/tools/buster/buster_extension_firefox")
    
    # Start Camoufox in virtual headless mode
    print("Starting Camoufox (Buster + Whisper)...")
    with Camoufox(
        headless="virtual",
        virtual_display="auto",
        addons=[buster_addon] if buster_addon else []
    ) as browser:
        # Create context with English locale
        context = browser.new_context(
            locale="en-US",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
        )
        
        # Intercept reCAPTCHA api2 requests
        print("Intercepting reCAPTCHA api2 requests...")
        def _recaptcha_route(route):
            url = route.request.url
            if "hl=" in url:
                new_url = url.replace("hl=nl", "hl=en").replace("hl=de", "hl=en")
            else:
                new_url = url + ("&" if "?" in url else "?") + "hl=en"
            route.continue_(url=new_url)
        context.route("**/recaptcha/api2/**", _recaptcha_route)
        
        page = context.new_page()
        
        # Navigate to target URL
        print(f"Navigating to {target_url}...")
        page.goto(target_url, wait_until="domcontentloaded", timeout=timeout)
        page.wait_for_timeout(3000)
        save_screenshot(page, "01_target_page")
        
        # Find reCAPTCHA iframe and solve it
        print("Looking for reCAPTCHA...")
        
        # Force English language on reCAPTCHA
        page.evaluate("""
            const iframes = document.querySelectorAll('iframe');
            iframes.forEach(frame => {
                const src = frame.getAttribute('src');
                if (src && src.includes('recaptcha/api2/anchor')) {
                    let newSrc = src.replace(/&hl=[^&]*/g, '').replace(/\\?hl=[^&]*/g, '');
                    newSrc += (newSrc.includes('?') ? '?' : '?') + 'hl=en';
                    frame.setAttribute('src', newSrc);
                }
            });
        """)
        page.wait_for_timeout(2000)
        
        # Find the reCAPTCHA anchor iframe - wait for it to appear
        print("Waiting for reCAPTCHA iframe...")
        anchor_frame = None
        for attempt in range(10):
            try:
                # Try to find by URL pattern
                anchor_frame = page.frame("**/recaptcha/api2/anchor")
                if anchor_frame:
                    print("Found reCAPTCHA via URL pattern")
                    break
            except:
                pass
            # Fallback: search through frames
            for frame in page.frames:
                if "recaptcha/api2" in frame.url and "bframe" not in frame.url:
                    anchor_frame = frame
                    print(f"Found reCAPTCHA via frame search: {frame.url}")
                    break
            if anchor_frame:
                break
            print(f"Waiting for reCAPTCHA... attempt {attempt+1}/10")
            page.wait_for_timeout(3000)
        
        if not anchor_frame:
            # Last resort: look for checkbox on main page
            print("Could not find reCAPTCHA iframe, trying to locate checkbox directly...")
            try:
                checkbox = page.locator(".recaptcha-checkbox-border").first
                if checkbox.is_visible(timeout=5000):
                    anchor_frame = page.main_frame
                    print("Found reCAPTCHA checkbox directly on page")
            except:
                pass
        
        if not anchor_frame:
            print("⚠ No reCAPTCHA found - page may not need solving")
            save_screenshot(page, "no_recaptcha")
            return True
        
        # Click reCAPTCHA checkbox
        print("Clicking reCAPTCHA checkbox...")
        anchor_frame.locator(".recaptcha-checkbox-border").click()
        page.wait_for_timeout(3000)
        save_screenshot(page, "02_checkbox_clicked")
        
        # Solve via Buster extension (primary method)
        print("Attempting Buster solver...")
        audio_btn = anchor_frame.locator("#recaptcha-audio-button")
        if audio_btn.count() > 0 and audio_btn.is_visible():
            audio_btn.click()
            page.wait_for_timeout(3000)
            save_screenshot(page, "03_audio_solved_retry_1")
            
            # Check if solved
            if anchor_frame.locator(".recaptcha-checkbox-checked").count() > 0:
                print("✓ reCAPTCHA solved via Buster!")
                save_screenshot(page, "04_solved")
                return True
            else:
                print("Buster didn't solve it - trying audio challenge + Whisper fallback...")
                # Audio challenge + Whisper fallback
                audio_source = anchor_frame.locator("audio#audio-source")
                if audio_source.count() > 0:
                    audio_btn.click()
                    page.wait_for_timeout(3000)
                    save_screenshot(page, "05_audio_challenge")

                    # Download and transcribe audio
                    mp3_path = f"/tmp/captcha_audio_{int(time.time())}.mp3"
                    audio_src = audio_source.get_attribute("src")
                    resp = requests.get(audio_src, timeout=30)
                    resp.raise_for_status()
                    with open(mp3_path, "wb") as f:
                        f.write(resp.content)

                    transcription = transcribe_audio(mp3_path, whisper_model)
                    if transcription:
                        # Fill the audio response field
                        page.evaluate("""(transcription) => {
                            const ta = document.querySelector('#audio-response');
                            if (ta) ta.value = transcription;
                        }""", transcription)
                        page.wait_for_timeout(1000)
                        save_screenshot(page, "06_audio_submitted")

                        # Verify checkbox is now checked
                        if anchor_frame.locator(".recaptcha-checkbox-checked").count() > 0:
                            print("\u2713 reCAPTCHA solved via audio challenge!")
                            save_screenshot(page, "07_audio_solved")
                            return True

        # If still not solved, try the fallback path
        print("Still not solved - trying fallback path...")
        # Look for submit button
        submit_btn = page.locator("text=Verstuur|text=Indienen|text=Submit|text=Send")
        if submit_btn.count() > 0 and submit_btn.first.is_visible():
            submit_btn.first.click()
            page.wait_for_timeout(3000)
            save_screenshot(page, "08_form_submitted")
        
        # Final check
        if anchor_frame.locator(".recaptcha-checkbox-checked").count() > 0:
            print("✓ reCAPTCHA solved (via fallback)")
            save_screenshot(page, "09_final_solved")
            return True
        
        print("❌ Failed to solve reCAPTCHA after 3 attempts")
        save_screenshot(page, "10_failed")
        return False


def main():
    parser = argparse.ArgumentParser(description="Solve reCAPTCHA checkbox and screenshot result.")
    parser.add_argument("--url", required=True, help="Target URL with reCAPTCHA")
    parser.add_argument("--timeout", type=int, default=180000, help="Timeout in milliseconds")
    parser.add_argument("--no-screenshots", action="store_true", help="Skip screenshot saving")
    args = parser.parse_args()
    
    if not args.url.startswith("http://") and not args.url.startswith("https://"):
        print("❌ Invalid URL - must start with http:// or https://")
        sys.exit(1)
    
    print("=" * 60)
    print("ReCAPTCHA Solver - Standalone (no UrbanFix required)")
    print(f"Target: {args.url}")
    print("=" * 60)
    
    try:
        success = solve_recaptcha(args.url, args.timeout)
        if success:
            print("\n✅ Success! Result screenshot saved to:")
            print(f"   {screenshots_dir}")
            sys.exit(0)
        else:
            print("\n❌ Failed to solve reCAPTCHA")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
