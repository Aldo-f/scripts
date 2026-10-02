"""
Rich Structured Logging for Form Automation
Logs to file and console with JSON-like structure for easy parsing
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure logs directory exists
LOG_DIR = Path.home() / "scripts" / "form-automation-v2" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Screenshots directory
SCREENSHOT_DIR = LOG_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Audio buffer directory
AUDIO_BUFFER_DIR = LOG_DIR / "audio_buffer"
AUDIO_BUFFER_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
LOG_FILE = LOG_DIR / "submissions.log"

# Custom formatter to output JSON lines
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        # Add extra fields if present
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                              'levelname', 'levelno', 'lineno', 'module', 'msecs',
                              'message', 'msg', 'name', 'pathname', 'process', 'processName',
                              'relativeCreated', 'thread', 'threadName', 'exc_info', 'exc_text',
                              'stack_info']:
                    log_entry[key] = value
        return json.dumps(log_entry)

def setup_logging():
    """Set up the logger with file and console handlers."""
    logger = logging.getLogger("form_automation")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers = []
    
    # File handler with JSON formatting
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    
    # Console handler with simple formatting for readability
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Set up the logger
logger = setup_logging()

def log_with_context(level, message, **kwargs):
    """Log a message with additional context fields."""
    extra = kwargs
    if level == 'debug':
        logger.debug(message, extra=extra)
    elif level == 'info':
        logger.info(message, extra=extra)
    elif level == 'warning':
        logger.warning(message, extra=extra)
    elif level == 'error':
        logger.error(message, extra=extra)
    elif level == 'critical':
        logger.critical(message, extra=extra)

def capture_screenshot(page, step_name: str) -> str:
    """Capture a screenshot and save it with timestamp and step name."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"{timestamp}_{step_name}.png"
    filepath = SCREENSHOT_DIR / filename
    try:
        page.screenshot(path=str(filepath))
        logger.info(f"Screenshot saved: {filepath}", extra={"screenshot_path": str(filepath), "step": step_name})
        return str(filepath)
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return ""