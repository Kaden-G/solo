"""Decision gate system — centralized pause/resume via Prefect RunInput."""

from prefect import pause_flow_run
from prefect.input import RunInput

from engine.state_loader import save_state_file


class DecisionRequired(Exception):
    """Raised by tasks when a human decision is needed before proceeding."""

    def __init__(self, summary: str, options: list[str]):
        self.summary = summary
        self.options = options
        super().__init__(f"Decision required: {summary} (options: {options})")


class DecisionInput(RunInput):
    """Schema for human decision input via Prefect UI."""

    choice: str


def require_decision(summary: str, options: list[str]) -> str:
    """Pause the flow and wait for a human decision via Prefect UI.

    Only called from flows/autonomous_flow.py — never from tasks directly.
    """
    description = f"**{summary}**\n\nOptions:\n"
    for opt in options:
        description += f"- `{opt}`\n"

    result: DecisionInput = pause_flow_run(
        wait_for_input=DecisionInput,
        timeout=86400,
    )
    return result.choice


def save_decision(summary: str, choice: str) -> None:
    """Persist a decision to state/decisions/ so tasks can read it."""
    safe_name = summary.lower().replace(" ", "_")[:60]
    content = f"# Decision: {summary}\n\nChoice: {choice}\n"
    save_state_file(f"decisions/{safe_name}.md", content)
