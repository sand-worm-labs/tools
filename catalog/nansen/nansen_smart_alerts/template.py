# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

NAME = "{{name}}".strip()
ALERT_TYPE = "{{alert_type}}"
TIME_WINDOW = "{{time_window}}"
CHAINS = "{{chains}}"
CHANNEL_TYPE = "{{channel_type}}"
CHANNEL_TARGET = "{{channel_target}}".strip()
DESCRIPTION = "{{description}}".strip()
IS_ENABLED = "{{is_enabled}}"

ALLOWED_ALERT_TYPES = {"common-token-transfer", "sm-token-flows", "smart-contract-call"}
ALLOWED_TIME_WINDOWS = {"realtime", "1m", "5m", "10m", "30m", "1h", "4h", "12h", "1d", "1w"}
ALLOWED_CHANNEL_TYPES = {"telegram", "slack", "discord", "webhook"}

if not NAME:
    raise ValueError("name is required")
if ALERT_TYPE not in ALLOWED_ALERT_TYPES:
    raise ValueError(f"Unsupported alert_type: {ALERT_TYPE!r}")
if TIME_WINDOW not in ALLOWED_TIME_WINDOWS:
    raise ValueError(f"Unsupported time_window: {TIME_WINDOW!r}")
if CHANNEL_TYPE not in ALLOWED_CHANNEL_TYPES:
    raise ValueError(f"Unsupported channel_type: {CHANNEL_TYPE!r}")
if not CHANNEL_TARGET:
    raise ValueError("channel_target is required")
if IS_ENABLED not in {"true", "false"}:
    raise ValueError(f"Invalid is_enabled: {IS_ENABLED!r}")

chains = [c.strip() for c in CHAINS.split(",") if c.strip()]
if not chains:
    raise ValueError("chains is required")

channel_key = "chatId" if CHANNEL_TYPE == "telegram" else "webhookUrl"
events_by_type = {
    "common-token-transfer": None,
    "sm-token-flows": ["sm-token-flows"],
    "smart-contract-call": ["smart-contract-call"],
}

data = {"chains": chains, "inclusion": {}, "exclusion": {}}
if events_by_type[ALERT_TYPE]:
    data["events"] = events_by_type[ALERT_TYPE]

body = {
    "name": NAME,
    "type": ALERT_TYPE,
    "timeWindow": TIME_WINDOW,
    "channels": [{"type": CHANNEL_TYPE, "data": {channel_key: CHANNEL_TARGET}}],
    "data": data,
    "isEnabled": IS_ENABLED == "true",
}
if DESCRIPTION:
    body["description"] = DESCRIPTION

response = requests.post(
    "https://api.nansen.ai/api/v1/smart-alert",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

# The success response body is {}; the useful confirmation is in the credit headers.
{{__df_name}} = pd.DataFrame([{
    "name": NAME,
    "type": ALERT_TYPE,
    "time_window": TIME_WINDOW,
    "chains": ", ".join(chains),
    "is_enabled": IS_ENABLED == "true",
    "credits_used": response.headers.get("X-Nansen-Credits-Used"),
    "credits_remaining": response.headers.get("X-Nansen-Credits-Remaining"),
    "request_id": response.headers.get("X-Request-Id"),
}])
{{__df_name}}
