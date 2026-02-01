"""State directory helpers — read/write files under state/."""

from pathlib import Path

import yaml

STATE_DIR = Path(__file__).resolve().parent.parent / "state"


def load_state_file(name: str) -> str:
    """Read a file from state/ and return its contents."""
    path = STATE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"State file not found: {path}")
    return path.read_text()


def save_state_file(name: str, content: str) -> None:
    """Write content to a file under state/."""
    path = STATE_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def load_decision_gates() -> list[dict]:
    """Parse templates/DECISION_GATES.yml and return gate definitions."""
    gates_path = Path(__file__).resolve().parent.parent / "templates" / "DECISION_GATES.yml"
    with open(gates_path) as f:
        data = yaml.safe_load(f)
    return data.get("gates", [])


def list_decisions() -> dict[str, str]:
    """Return a map of decision filenames to their content in state/decisions/."""
    decisions_dir = STATE_DIR / "decisions"
    results = {}
    for path in decisions_dir.glob("*.md"):
        results[path.stem] = path.read_text()
    return results


def decision_exists(summary: str) -> bool:
    """Check whether a decision has already been recorded for the given summary."""
    safe_name = summary.lower().replace(" ", "_")[:60]
    return (STATE_DIR / "decisions" / f"{safe_name}.md").exists()
