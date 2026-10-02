#!/usr/bin/env python3
"""
Self-improving form automation with AI enhancement
Runs continuously, improving via FreLLM API and local Whisper for CAPTCHA
"""
import sys
import os
import signal
import time
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import and setup proper logging
from logger import logger, setup_logging

# Daemon file for graceful shutdown
DAEMON_FILE = Path.home() / "scripts" / "form-automation-v2" / "data" / "STOP"

def signal_handler(sig, frame):
    """Handle stop signal."""
    print("\nStop signal received. Shutting down gracefully...")
    if DAEMON_FILE.exists():
        DAEMON_FILE.unlink()
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def main():
    """Main entry point."""
    # Parse args
    import argparse
    parser = argparse.ArgumentParser(description="Self-improving form automation")
    parser.add_argument("--batch", type=int, default=1, help="Batch size")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between submissions")
    parser.add_argument("--browser_type", choices=["chromium", "camoufox"], default="chromium")
    args = parser.parse_args()

    DAEMON_FILE.touch(exist_ok=True)

    # Import after path setup
    from submission_flow import SubmissionFlow

    logger.info("Starting self-improving form automation system v2.0")

    automation = SubmissionFlow()

    try:
        # Run single batch
        automation.run_batch(args.batch, args.delay, args.browser_type)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        print(f"Stats: {automation.success_count} success, {automation.failure_count} failed")

if __name__ == "__main__":
    main()