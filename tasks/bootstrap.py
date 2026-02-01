"""Bootstrap task — verify intake artifacts exist and initialize TRACE.json."""

from prefect import task

from engine.context import get_state_dir
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
    state_dir = get_state_dir()

    # Verify all required inputs exist (belt-and-suspenders with flow check)
    missing = [f for f in REQUIRED_FILES if not (state_dir / f).exists()]
    if missing:
        raise RuntimeError(f"Bootstrap failed — missing intake artifacts: {missing}")

    # Reset TRACE.json for this run
    trace_path = state_dir / "TRACE.json"
    trace_path.write_text("[]\n")

    # Ensure output directories exist
    for subdir in ("designs", "implementations", "tests", "decisions"):
        (state_dir / subdir).mkdir(parents=True, exist_ok=True)

    present = [f for f in REQUIRED_FILES if (state_dir / f).exists()]
    trace(
        task="bootstrap",
        inputs=present,
        outputs=["TRACE.json"],
    )
