"""Bootstrap task — copy templates to state/inputs/, initialize TRACE.json."""

import shutil
from pathlib import Path

from prefect import task

from engine.state_loader import STATE_DIR
from engine.tracer import trace

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


@task(name="bootstrap")
def bootstrap_project() -> None:
    """Copy all template files into state/inputs/ and reset TRACE.json."""
    inputs_dir = STATE_DIR / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for template in TEMPLATES_DIR.glob("*.md"):
        dest = inputs_dir / template.name
        shutil.copy2(template, dest)
        copied.append(f"inputs/{template.name}")

    # Copy DECISION_GATES.yml
    gates_src = TEMPLATES_DIR / "DECISION_GATES.yml"
    if gates_src.exists():
        gates_dest = inputs_dir / "DECISION_GATES.yml"
        shutil.copy2(gates_src, gates_dest)
        copied.append("inputs/DECISION_GATES.yml")

    # Reset TRACE.json
    trace_path = STATE_DIR / "TRACE.json"
    trace_path.write_text("[]\n")

    trace(
        task="bootstrap",
        inputs=[str(p.relative_to(TEMPLATES_DIR.parent)) for p in TEMPLATES_DIR.glob("*") if p.is_file()],
        outputs=copied,
    )
