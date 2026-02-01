"""Bootstrap task — verify intake artifacts exist and initialize TRACE.json."""

from pathlib import Path

from prefect import task

from engine.state_loader import STATE_DIR
from engine.tracer import trace

REQUIRED_FILES = [
    "inputs/project_spec.yml",
    "inputs/REQUIREMENTS.md",
    "inputs/CONSTRAINTS.md",
    "inputs/NON_GOALS.md",
    "inputs/ACCEPTANCE_CRITERIA.md",
]


@task(name="bootstrap")
def bootstrap_project() -> None:
    """Verify all intake artifacts are present, reset TRACE.json, log bootstrap."""
    # Verify all required inputs exist (belt-and-suspenders with flow check)
    missing = [f for f in REQUIRED_FILES if not (STATE_DIR / f).exists()]
    if missing:
        raise RuntimeError(f"Bootstrap failed — missing intake artifacts: {missing}")

    # Reset TRACE.json for this run
    trace_path = STATE_DIR / "TRACE.json"
    trace_path.write_text("[]\n")

    # Ensure output directories exist
    for subdir in ("designs", "implementations", "tests", "decisions"):
        (STATE_DIR / subdir).mkdir(parents=True, exist_ok=True)

    present = [f for f in REQUIRED_FILES if (STATE_DIR / f).exists()]
    trace(
        task="bootstrap",
        inputs=present,
        outputs=["TRACE.json"],
    )
