# freellm-proxy — ABANDONED

Status: Proxy works (port 9888 → freellm gateway, 283 models). Cursor CLI `agent` cannot be redirected.

## Why abandoned
- `agent` (Cursor CLI v2026.09.10) uses Cursor's private auth (`CURSOR_API_KEY` → `api2.cursor.sh/auth/exchange_user_api_key`), not OpenAI-compatible `/v1/chat/completions`.
- `agent --endpoint freellm...` returns "API key invalid" (Cursor rejects FreeLLM key).
- Usage error (`You've hit your usage limit`) comes from Cursor backend, not gateway.
- LiteLLM install blocked (malicious package flag on unpinned version).
- Custom proxy (`custom_freellm_proxy.py`) handles SDK/openai clients only; agent CLI protocol is incompatible.

## What's working
- `~/scripts/freellm-proxy/custom_freellm_proxy.py` — Python proxy (systemd: `app-proxy-cursor-freellmapi.service`, active)
- SDK path verified: `uv run python3 -c "import openai; ..."` → 283 models from gateway
- Persistent env: `~/.config/fish/config.fish` (`OPENAI_BASE_URL`, `OPENAI_API_KEY`)

## What's not working
- `agent "..." --trust` → Cursor usage limit / backend error (not gateway)
- No safe LiteLLM version pinned to build a bridge

## Files
- `custom_freellm_proxy.py` — proxy
- `/etc/systemd/system/app-proxy-cursor-freellmapi.service` — auto-start enabled
- `~/tdd_freellm_plan.md` — full TDD log (red → blocked → alt 3)

## Next options (not pursued)
1. LiteLLM with pinned safe version (if user provides exact non-affected version)
2. Cursor IDE Settings → Override Base URL (not CLI agent)
3. Wait until Cursor Pro / usage reset (10/5/2026 per error)
