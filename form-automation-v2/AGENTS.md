# Form Automation v2 — Self-Improving Google Forms Bot

## OVERVIEW
Daemon-driven Google Form submission system with AI config patching via FreLLM API, local Whisper.cpp audio CAPTCHA solving, and Tesseract OCR image CAPTCHA fallback. Browser layer is simulation-only (dummy).

## SRC MODULES
- `submission_flow.py` — `SubmissionFlow` class: batch runner, counter persistence in `data/counter.json`, triggers AI improvement at 10 failures
- `browser_manager.py` — **DUMMY** simulation browser (random success/failure, no real Playwright/Camoufox yet). Replace with real impl before production use.
- `api_integration.py` — FreLLM API client (`http://192.168.0.5:3001/v1`, Bearer token), patch generation from failure patterns, config application, health checks
- `ai_improver.py` — Failure pattern analysis from `logs/submissions.log`, FreLLM `/chat/completions` prompt generation, YAML config patching with backup
- `whisper_solver.py` — Local whisper.cpp audio CAPTCHA transcription via ffmpeg preprocessing (16kHz mono WAV), human fallback prompt
- `tesseract_ocr.py` — Image CAPTCHA OCR with PIL preprocessing (grayscale, contrast, sharpen, resize)
- `logger.py` — JSON-line structured logging to `logs/submissions.log`, screenshot capture to `logs/screenshots/`

## CONFIG & DATA
- `config/config_v2.yaml` — Form URL, field selectors/values, browser type (chromium/camoufox), CAPTCHA solver toggles, AI improvement settings
- `data/counter.json` — Submission counter with last timestamp
- `data/STOP` — Daemon control file (touch to stop, removed on SIGTERM/SIGINT)
- `logs/submissions.log` — JSON lines, parsed by AI improver for failure patterns
- `logs/screenshots/`, `logs/audio_buffer/` — Debug artifacts

## COMMANDS
```bash
# Run single batch (default 1 submission, 0.1s delay)
python3 scripts/run_automation.py --batch 5 --delay 2.0 --browser_type chromium

# Continuous run (stop via data/STOP or SIGTERM)
python3 scripts/run_automation.py --batch 1 --delay 0.1

# Test FreLLM API connectivity (health, streaming, improve endpoints)
python3 test_api.py

# Run AI improvement loop standalone
python3 -c "from src.ai_improver import run_ai_improvement_loop; run_ai_improvement_loop()"
```

## NOTES
- `browser_manager.py` is explicitly a simulation stub — real browser automation not yet wired
- AI improvement triggers automatically after 10 consecutive failures, then resets counter
- Config patches are applied with a `.yaml.bak` backup created before modification
- Dependencies in `requirements.txt`; venv at `venv/` (already installed)
- FreLLM API token is hardcoded in `api_integration.py` and `ai_improver.py` — rotate before production