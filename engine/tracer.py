"""Traceability spine — append structured entries to state/TRACE.json."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = Path(__file__).resolve().parent.parent / "state"
TRACE_PATH = STATE_DIR / "TRACE.json"


def trace(
    task: str,
    inputs: list[str],
    outputs: list[str],
    model: str | None = None,
    prompt_hash: str | None = None,
) -> None:
    """Append a trace entry to TRACE.json."""
    entries = _load_trace()
    entry = {
        "task": task,
        "inputs": inputs,
        "outputs": outputs,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if model:
        entry["model"] = model
    if prompt_hash:
        entry["prompt_hash"] = prompt_hash
    entries.append(entry)
    TRACE_PATH.write_text(json.dumps(entries, indent=2) + "\n")


def hash_prompt(prompt_text: str) -> str:
    """Return a SHA-256 hash of a prompt string for traceability."""
    return hashlib.sha256(prompt_text.encode()).hexdigest()[:16]


def _load_trace() -> list[dict]:
    """Load the current TRACE.json entries."""
    if not TRACE_PATH.exists():
        return []
    text = TRACE_PATH.read_text().strip()
    if not text:
        return []
    return json.loads(text)
