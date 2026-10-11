# Sandworm Power Toolbox — {{__tool_name}}
import json
import os

import pandas as pd
import requests

TEXT = "{{text}}".strip()
AGENT_MODE = "{{agent_mode}}"
CONVERSATION_ID = "{{conversation_id}}".strip()

ALLOWED_AGENT_MODES = {"fast", "expert"}

if not TEXT:
    raise ValueError("text is required")
if AGENT_MODE not in ALLOWED_AGENT_MODES:
    raise ValueError(f"Unsupported agent_mode: {AGENT_MODE!r}")

body = {"text": TEXT}
if CONVERSATION_ID:
    body["conversation_id"] = CONVERSATION_ID

# The agent streams Server-Sent Events rather than returning a single JSON body.
response = requests.post(
    f"https://api.nansen.ai/api/v1/agent/{AGENT_MODE}",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=120,
    stream=True,
)
response.raise_for_status()

answer_parts = []
conversation_id = None
tool_calls = []
for line in response.iter_lines(decode_unicode=True):
    if not line or not line.startswith("data: "):
        continue
    payload = line[len("data: "):]
    if payload == "[DONE]":
        break
    event = json.loads(payload)
    event_type = event.get("type")
    if event_type == "delta":
        answer_parts.append(event.get("text", ""))
    elif event_type == "tool_call":
        tool_calls.append(event.get("name"))
    elif event_type == "finish":
        conversation_id = event.get("conversation_id")
    elif event_type == "error":
        raise ValueError(f"Nansen agent error: {event.get('error')}")

answer = "".join(answer_parts)
{{__df_name}} = pd.DataFrame([{
    "answer": answer,
    "conversation_id": conversation_id,
    "tool_calls": ", ".join(tool_calls),
    "tool_call_count": len(tool_calls),
    "answer_word_count": len(answer.split()),
}])
{{__df_name}}
