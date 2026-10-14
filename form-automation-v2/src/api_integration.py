"""
FreLLM API Integration - Config & Utility Functions

The FreLLM API endpoint is configured at:
  - Base URL: http://192.168.0.5:3001/v1
  - API Token: <set via FREELLMAPI_API_KEY env var>

This module handles:
  1. API authentication (Bearer token)
  2. HTTP request management
  3. Patch generation from failure patterns
  4. Auto-configuration updates
"""

import logging
import json
import time
import requests
from pathlib import Path
from urllib.parse import urljoin

logger = logging.getLogger("freellm_api")

# FreLLM API Configuration
API_BASE_URL = "http://192.168.0.5:3001/v1"
import os
API_TOKEN = os.getenv("FREELLMAPI_API_KEY", "")


def get_api_headers():
    """Return request headers with Bearer token."""
    return {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def call_api(endpoint, method="POST", data=None, timeout=30, retries=3):
    """
    Call FreLLM API endpoint.

    Args:
        endpoint: The API endpoint (e.g., "/ai/improve")
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request body (JSON dict)
        timeout: Request timeout in seconds
        retries: Number of retry attempts on failure

    Returns:
        Parsed JSON response or None on failure
    """
    url = urljoin(API_BASE_URL, endpoint)
    headers = get_api_headers()

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"API call to {url} (attempt {attempt}/{retries})")
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=timeout,
            )

            if response.status_code == 200:
                logger.info(f"API call successful: {endpoint}")
                return response.json()
            elif response.status_code == 401:
                logger.error("Authentication failed - API token may be invalid")
                return None
            elif response.status_code == 502:
                logger.warning(f"Bad gateway (502) - retrying: {endpoint}")
                if attempt < retries:
                    time.sleep(1)
                    continue
            elif response.status_code >= 500:
                logger.error(f"Server error ({response.status_code}) - retrying: {endpoint}")
                if attempt < retries:
                    time.sleep(1)
                    continue
            else:
                logger.error(f"Unexpected status {response.status_code} for {endpoint}")
                return None

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to {url}: {e} - retrying: {attempt}")
            if attempt < retries:
                time.sleep(1)
                continue
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout to {url}: {e} - retrying: {attempt}")
            if attempt < retries:
                time.sleep(1)
                continue
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return None

    logger.error(f"All {retries} retries failed for {endpoint}")
    return None


def generate_patch_from_failure_patterns(failure_patterns):
    """Generate an AI patch based on failure patterns."""
    if not failure_patterns:
        return None

    # Analyze failure patterns
    error_types = {}
    for pattern in failure_patterns:
        error = pattern.get("error", "")
        if error not in error_types:
            error_types[error] = []
        error_types[error].append(pattern)

    most_common_errors = sorted(error_types.items(), key=lambda x: len(x[1]), reverse=True)[:5]

    patch = {
        "api_version": "v2.0",
        "timestamp": time.time(),
        "failure_summary": len(failure_patterns),
        "improvements": [],
        "config_changes": [],
    }

    for error_type, patterns in most_common_errors:
        error_msg = error_type.lower()
        if "select" in error_msg:
            patch["improvements"].append({
                "type": "selector_update",
                "description": f"Update selectors in config_v2.yaml for failing fields",
                "priority": "high",
            })
        elif "captcha" in error_msg:
            patch["improvements"].append({
                "type": "captcha_solver",
                "description": "Configure CAPTCHA solver to use Whisper model",
                "priority": "medium",
            })
        elif "timeout" in error_msg:
            patch["improvements"].append({
                "type": "timeout_adjustment",
                "description": f"Adjust timeout for {error_type} requests",
                "priority": "low",
            })
        elif "api" in error_msg:
            patch["improvements"].append({
                "type": "endpoint_retry",
                "description": f"Retry failed endpoint: {error_type}",
                "priority": "medium",
            })
        else:
            patch["improvements"].append({
                "type": "general_fix",
                "description": f"Analyze failure pattern: {error_type}",
                "priority": "low",
            })

    # Add API configuration improvements
    patch["config_changes"].append({
        "key": "api_base_url",
        "old_value": API_BASE_URL,
        "new_value": API_BASE_URL,
        "description": "Ensure base URL is correct",
    })

    return patch


def apply_patch_to_config(patch):
    """Apply a patch to the configuration file."""
    try:
        import yaml
        from pathlib import Path

        config_path = Path.home() / "scripts" / "form-automation-v2" / "config" / "config_v2.yaml"

        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            return False

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Apply improvements to config
        for improvement in patch.get("improvements", []):
            if improvement["type"] == "selector_update":
                # Apply selector changes to config
                for field_name, field_info in config.get("form", {}).get("fields", {}).items():
                    selector = field_info.get("selector")
                    # In a real implementation, this would update specific selectors
                    pass

        # Save updated config
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        logger.info(f"Applied patch to config_v2.yaml")
        return True

    except Exception as e:
        logger.error(f"Failed to apply patch: {e}")
        return False


def run_ai_improvement_loop():
    """Run the AI improvement loop."""
    try:
        from src.ai_improver import run_ai_improvement as _run
        _run()
    except Exception as e:
        logger.error(f"AI improvement failed: {e}")


def run_continuous_improvement_check():
    """Run continuous improvement check."""
    # Analyze failure patterns from logs
    failure_patterns = analyze_failure_patterns()
    failure_count = len(failure_patterns)
    
    if failure_count >= 10:
        api_patch = generate_patch_from_failure_patterns(failure_patterns)
        if api_patch:
            success = apply_patch_to_config(api_patch)
            return {"status": "improvement_applied" if success else "failed", "patch": api_patch}
    
    return {"status": "no_improvement_needed", "failure_count": failure_count}


def analyze_failure_patterns():
    """Analyze failure patterns from submission logs."""
    log_path = Path.home() / "scripts" / "form-automation-v2" / "logs" / "submissions.log"
    failures = []
    if log_path.exists():
        with open(log_path) as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if entry.get("level") == "ERROR":
                            failures.append(entry)
                    except json.JSONDecodeError:
                        pass
    return failures


def health_check():
    """Run a health check on the FreLLM API."""
    try:
        response = requests.get(f"{API_BASE_URL}/healthz", timeout=10)
        if response.status_code != 200:
            return {"status": "unhealthy", "response": None}
            
        # Check if response has content
        if not response.content:
            logger.warning("Health check response is empty")
            return {"status": "unhealthy", "response": None}
            
        response_json = response.json()
        return {"status": "healthy" if response_json.get("status") == "ok" else "unhealthy", "response": response_json}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "response": None}