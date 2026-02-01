"""Verify task — check test results against acceptance criteria."""

from pathlib import Path

from prefect import task

from engine.llm_provider import get_provider
from engine.state_loader import load_state_file, save_state_file
from engine.tracer import hash_prompt, trace

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "templates" / "prompts"


@task(name="verify")
def verify_system() -> None:
    """Read test results and acceptance criteria, produce final verification report."""
    test_results = load_state_file("tests/TEST_RESULTS.md")
    acceptance = load_state_file("inputs/ACCEPTANCE_CRITERIA.md")
    requirements = load_state_file("inputs/REQUIREMENTS.md")

    prompt_template = (PROMPTS_DIR / "verify.txt").read_text()
    prompt = prompt_template.format(
        test_results=test_results,
        acceptance_criteria=acceptance,
        requirements=requirements,
    )

    provider = get_provider()
    p_hash = hash_prompt(prompt)
    verification = provider.generate(prompt)

    output_path = "tests/VERIFICATION.md"
    save_state_file(output_path, verification)

    trace(
        task="verify",
        inputs=["tests/TEST_RESULTS.md", "inputs/ACCEPTANCE_CRITERIA.md", "inputs/REQUIREMENTS.md"],
        outputs=[output_path],
        model=provider.model,
        prompt_hash=p_hash,
    )
