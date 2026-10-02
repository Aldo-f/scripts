"""
Form Submission Flow - Core form submission logic with AI improvement integration
"""
import logging
import time
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("form_automation.submission")


class SubmissionFlow:
    """Manages the complete form submission lifecycle."""

    def __init__(self, config_path=None):
        self.config = None
        self.config_path = config_path or (Path.home() / "scripts" / "form-automation-v2" / "config" / "config_v2.yaml")
        self.counter_file = Path.home() / "scripts" / "form-automation-v2" / "data" / "counter.json"
        self.counter = self._load_counter()
        self.submission_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.ai_improvement_threshold = 10
        self.failure_patterns = []

    def _load_counter(self) -> int:
        """Load submission counter from file."""
        if self.counter_file.exists():
            try:
                with open(self.counter_file) as f:
                    data = json.load(f)
                    return int(data.get("count", 0))
            except Exception as e:
                logger.warning(f"Could not load counter: {e}")
        return 0

    def _save_counter(self):
        """Persist counter to file."""
        try:
            self.counter_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.counter_file, "w") as f:
                json.dump({
                    "count": self.counter,
                    "last_submission": datetime.utcnow().isoformat() + "Z"
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save counter: {e}")

    def load_config(self):
        """Load form configuration from YAML."""
        try:
            import yaml
            with open(self.config_path) as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded config from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Use default minimal config
            self.config = {
                "form": {
                    "url": "https://forms.gle/example",
                    "fields": {},
                    "submit_selector": 'button[type="submit"]',
                    "confirmation_selector": '.recaptcha-success'
                }
            }

    def run_batch(self, batch_size: int = 1, delay: float = 2.0, browser_type="chromium"):
        """Run a batch of form submissions."""
        from browser_manager import BrowserManager

        if not self.config:
            self.load_config()

        form_config = self.config.get("form", {})
        form_url = form_config.get("url")
        field_config = form_config.get("fields", {})

        if not form_url:
            logger.error("No form URL in config")
            return False

        logger.info(f"Starting batch: {batch_size} submissions (counter: {self.counter})")

        # Initialize browser
        browser = BrowserManager(browser_type)
        try:
            browser.start_browser()

            for i in range(batch_size):
                self.submission_count += 1
                logger.info(f"Submission {i + 1}/{batch_size} (counter: {self.counter})")

                # Replace counter placeholder
                for field_name, field_info in field_config.items():
                    if "${counter}" in str(field_info.get("value", "")):
                        field_info["value"] = str(field_info["value"]).replace("${counter}", str(self.counter))

                # Submit form
                success = browser.submit_form(form_url, field_config)

                if success:
                    self.counter += 1
                    self.success_count += 1
                    logger.info(f"Submission {self.counter} SUCCESS")
                else:
                    self.failure_count += 1
                    logger.error(f"Submission {self.counter} FAILED")
                    # Record failure pattern for AI improvement
                    self.failure_patterns.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "counter": self.counter,
                        "url": form_url,  # Use known form URL instead of browser page
                    })

                self._save_counter()

                # Trigger AI improvement after threshold failures
                if self.failure_count >= self.ai_improvement_threshold:
                    logger.info(f"AI improvement triggered: {self.failure_count} failures")
                    self._run_ai_improvement()
                    self.failure_count = 0  # Reset after improvement attempt

                # Delay between submissions
                if i < batch_size - 1:
                    time.sleep(delay)

        finally:
            browser.close_browser()

        logger.info(f"Batch complete: {self.success_count} success, {self.failure_count} failures, counter: {self.counter}")
        return self.success_count > 0

    def _run_ai_improvement(self):
        """Run AI improvement loop to analyze failures and apply patches."""
        try:
            from ai_improver import run_ai_improvement_loop
            run_ai_improvement_loop()
        except Exception as e:
            logger.error(f"AI improvement failed: {e}")

    def run_continuous(self, max_submissions=None, delay=2.0, browser_type="chromium"):
        """Run continuously until stopped or max reached."""
        total = 0
        while max_submissions is None or total < max_submissions:
            if self.run_batch(1, delay, browser_type):
                total += 1
            else:
                logger.warning("Submission failed, retrying...")
                time.sleep(5)

            # Check for stop signal
            stop_file = Path.home() / "scripts" / "form-automation-v2" / "data" / "STOP"
            if stop_file.exists():
                logger.info("Stop signal received")
                stop_file.unlink()
                break

    def show_stats(self):
        """Display current statistics."""
        print(f"\n{'='*50}")
        print(f"FORM AUTOMATION STATISTICS")
        print(f"{'='*50}")
        print(f"Current counter:     {self.counter}")
        print(f"Total submissions:   {self.submission_count}")
        print(f"Successful:          {self.success_count}")
        print(f"Failed:              {self.failure_count}")
        print(f"Success rate:        {self.success_count/max(1,self.submission_count)*100:.1f}%")
        print(f"Failure patterns:    {len(self.failure_patterns)} recorded")
        print(f"{'='*50}\n")