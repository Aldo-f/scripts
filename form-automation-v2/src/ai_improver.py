"""
AI Improvement Engine for Form Automation
Analyzes failure patterns and generates config patches via FreLLM API
"""
import json
import time
import logging
import sys
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("form_automation.ai_improver")

# FreLLM API Configuration
API_BASE_URL = "http://192.168.0.5:3001/v1"
import os
API_TOKEN = os.getenv("FREELLMAPI_API_KEY", "")

# Config file paths
CONFIG_PATH = Path.home() / "scripts" / "form-automation-v2" / "config" / "config_v2.yaml"
BACKUP_PATH = CONFIG_PATH.with_suffix(".yaml.bak")
SUBMISSION_LOG = Path.home() / "scripts" / "form-automation-v2" / "logs" / "submissions.log"


def call_freellm_api(endpoint, payload, timeout=60):
    """Call FreLLM API endpoint with proper authentication."""
    import requests
    
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        logger.info(f"Calling FreLLM API: {url}")
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return None


def load_failure_patterns():
    """Load and parse failure patterns from submission log."""
    failures = []
    if not SUBMISSION_LOG.exists():
        return failures
    
    try:
        with open(SUBMISSION_LOG) as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if entry.get("level") == "ERROR" and "FAILED" in entry.get("message", ""):
                            failures.append({
                                "timestamp": entry.get("timestamp"),
                                "counter": entry.get("counter"),
                                "message": entry.get("message"),
                                "module": entry.get("module"),
                                "function": entry.get("function")
                            })
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        logger.error(f"Failed to read submission log: {e}")
    
    return failures


def analyze_failure_patterns(failures):
    """Analyze failure patterns and group by type."""
    if not failures:
        return {}
    
    # Group by error type
    error_groups = {}
    for f in failures:
        msg = f.get("message", "")
        if "CAPTCHA" in msg or "captcha" in msg:
            key = "captcha_failure"
        elif "selector" in msg.lower() or "element" in msg.lower():
            key = "selector_failure"
        elif "timeout" in msg.lower():
            key = "timeout_failure"
        elif "submit" in msg.lower():
            key = "submit_failure"
        elif "network" in msg.lower() or "connection" in msg.lower():
            key = "network_failure"
        else:
            key = "other_failure"
        
        if key not in error_groups:
            error_groups[key] = []
        error_groups[key].append(f)
    
    return error_groups


def generate_improvement_prompt(failures, error_groups):
    """Generate prompt for FreLLM to analyze failures and suggest config improvements."""
    
    # Build summary
    total_failures = len(failures)
    group_summary = "\n".join([f"  - {k}: {len(v)} occurrences" for k, v in error_groups.items()])
    
    # Recent failure details
    recent = failures[-5:] if len(failures) >= 5 else failures
    recent_details = "\n".join([
        f"  Counter {f.get('counter')}: {f.get('message')} (module: {f.get('module')}, function: {f.get('function')})"
        for f in recent
    ])
    
    prompt = f"""You are an AI assistant helping improve a Google Form automation script.
The script submits forms automatically but is experiencing failures.

## Failure Summary
Total failures: {total_failures}

## Failure Types
{group_summary}

## Recent Failure Details
{recent_details}

## Current Configuration (config_v2.yaml)
```yaml
form:
  url: "https://docs.google.com/forms/d/e/1FAIpQLSdvvFc-7Q3ZMGHBUUrBHtVO0tkKj0bUVrT-3sJYI4CIxoJ3RA/viewform"
  fields:
    email:
      selector: 'input[type="email"]'
      value: "chiefmommy@web-library.net"
    competition_question:
      selector: 'input[type="text"] >> nth=0'
      value: "Waarom bleef je niet voor mij?"
    tiebreaker_question:
      selector: 'input[type="text"] >> nth=1'
      value: "${counter}"
  submit:
    - selector: 'div[jsname="M2UYVd"]'
    - selector: 'div[role="button"]:has-text("Verzenden")'
    - selector: 'div[role="button"]:has-text("Envoyer")'
    - selector: 'div[role="button"]:has-text("Submit")'
  confirmation:
    - '.freebirdFormviewerViewResponseConfirmationMessage'

browser:
  type: "chromium"
  headless: false
  timeout: 30000

captcha:
  use_whisper: true
  use_tesseract: true
  use_buster: true
  manual_fallback: true
  audio_timeout: 60

ai_improvement:
  enabled: true
  failure_threshold: 10
  model: "auto"
  endpoint: "http://192.168.0.5:3001/v1"
  auto_apply_patches: true
  patch_types:
    - selector
    - timeout
    - retry
    - captcha
    - config
```

## Task
Analyze the failures and suggest specific improvements to the config_v2.yaml.
Return a JSON object with the following structure:

```json
{{
  "analysis": "Brief analysis of root causes",
  "improvements": [
    {{
      "type": "selector|timeout|retry|captcha|config",
      "priority": "high|medium|low",
      "description": "What to change and why",
      "config_path": "dot.notation.path.to.config",
      "old_value": "current value",
      "new_value": "suggested value",
      "reason": "Why this change helps"
    }}
  ]
}}
```

Focus on actionable config changes. Common issues:
- Selector changes due to Google Forms UI updates
- Timeout adjustments for slow pages/network
- CAPTCHA solver configuration
- Retry strategy improvements
- Browser configuration tweaks

Return ONLY the JSON object, no extra text."""
    
    return prompt


def call_freellm_for_improvements(failures):
    """Call FreLLM API to get improvement suggestions."""
    error_groups = analyze_failure_patterns(failures)
    prompt = generate_improvement_prompt(failures, error_groups)
    
    payload = {
        "model": "auto",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert in web automation and configuration optimization. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    result = call_freellm_api("/chat/completions", payload)
    
    if result and "choices" in result:
        content = result["choices"][0]["message"]["content"]
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Raw response: {content}")
    
    return None


def apply_patches(patches):
    """Apply improvement patches to config_v2.yaml."""
    try:
        import yaml
        
        # Create backup
        import shutil
        shutil.copy2(CONFIG_PATH, BACKUP_PATH)
        logger.info(f"Created backup: {BACKUP_PATH}")
        
        # Load current config
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f)
        
        applied = []
        for patch in patches:
            config_path = patch.get("config_path", "")
            old_value = patch.get("old_value")
            new_value = patch.get("new_value")
            
            if not config_path:
                logger.warning(f"Skipping patch without config_path: {patch}")
                continue
            
            # Navigate to config path
            keys = config_path.split(".")
            target = config
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                target = target[key]
            
            final_key = keys[-1]
            if final_key in target and target[final_key] == old_value:
                target[final_key] = new_value
                applied.append({
                    "path": config_path,
                    "old": old_value,
                    "new": new_value,
                    "reason": patch.get("reason")
                })
                logger.info(f"Applied patch: {config_path} = {new_value}")
            else:
                logger.warning(f"Patch mismatch at {config_path}: expected {old_value}, found {target.get(final_key)}")
        
        # Save updated config
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Applied {len(applied)} patches to config")
        return applied
        
    except Exception as e:
        logger.error(f"Failed to apply patches: {e}")
        return []


def run_ai_improvement_loop():
    """Main entry point for the AI improvement loop."""
    logger.info("=" * 60)
    logger.info("Starting AI Improvement Loop")
    logger.info("=" * 60)
    
    # Load failures
    failures = load_failure_patterns()
    logger.info(f"Loaded {len(failures)} failure entries from log")
    
    if len(failures) < 10:
        logger.info(f"Failure threshold (10) not met. Current: {len(failures)}")
        return {
            "status": "threshold_not_met",
            "failure_count": len(failures),
            "message": f"Need 10 failures, have {len(failures)}"
        }
    
    # Get AI suggestions
    logger.info("Requesting AI improvement suggestions from FreLLM...")
    ai_result = call_freellm_for_improvements(failures)
    
    if not ai_result:
        logger.error("Failed to get AI suggestions")
        return {
            "status": "api_failed",
            "failure_count": len(failures),
            "message": "FreLLM API call failed or returned invalid response"
        }
    
    logger.info(f"AI Analysis: {ai_result.get('analysis', 'No analysis provided')}")
    
    # Apply patches
    improvements = ai_result.get("improvements", [])
    if improvements:
        applied = apply_patches(improvements)
        logger.info(f"Successfully applied {len(applied)} patches")
        
        # Log applied patches
        for a in applied:
            logger.info(f"  {a['path']}: {a['old']} -> {a['new']} ({a['reason']})")
    else:
        logger.info("No specific improvements suggested by AI")
        applied = []
    
    return {
        "status": "completed",
        "failure_count": len(failures),
        "analysis": ai_result.get("analysis"),
        "improvements_suggested": len(improvements),
        "improvements_applied": len(applied),
        "applied_patches": applied
    }


def test_api_connection():
    """Test FreLLM API connection."""
    payload = {
        "model": "auto",
        "messages": [{"role": "user", "content": "Test"}],
        "max_tokens": 10
    }
    result = call_freellm_api("/chat/completions", payload, timeout=15)
    return result is not None


if __name__ == "__main__":
    # Configure logging for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    
    # Test API
    if test_api_connection():
        print("✓ FreLLM API connection successful")
    else:
        print("✗ FreLLM API connection failed")
        sys.exit(1)
    
    # Run improvement loop
    result = run_ai_improvement_loop()
    print(f"\nResult: {json.dumps(result, indent=2, default=str)}")