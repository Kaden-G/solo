"""Test task — validate the implementation against requirements."""

from prefect import task

from engine.context import get_prompts_dir
from engine.llm_provider import get_provider
from engine.state_loader import load_state_file, save_state_file
from engine.tracer import hash_prompt, trace


@task(name="test")
def test_system() -> None:
    """Read implementation from state/implementations/, run validation via LLM."""
    implementation = load_state_file("implementations/IMPLEMENTATION.md")
    requirements = load_state_file("inputs/REQUIREMENTS.md")
    acceptance = load_state_file("inputs/ACCEPTANCE_CRITERIA.md")

    prompt_template = (get_prompts_dir() / "test.txt").read_text()
    prompt = prompt_template.format(
        implementation=implementation,
        requirements=requirements,
        acceptance_criteria=acceptance,
    )

    provider = get_provider()
    p_hash = hash_prompt(prompt)
    test_results = provider.generate(prompt)

    output_path = "tests/TEST_RESULTS.md"
    save_state_file(output_path, test_results)

    trace(
        task="test",
        inputs=["implementations/IMPLEMENTATION.md", "inputs/REQUIREMENTS.md", "inputs/ACCEPTANCE_CRITERIA.md"],
        outputs=[output_path],
        model=provider.model,
        prompt_hash=p_hash,
    )
