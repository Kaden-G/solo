"""Implement task — LLM generates code from the approved design."""

from prefect import task

from engine.context import get_prompts_dir
from engine.llm_provider import get_provider
from engine.state_loader import load_state_file, save_state_file
from engine.tracer import hash_prompt, trace


@task(name="implement")
def implement_system() -> None:
    """Read architecture from state/designs/, generate implementation via LLM."""
    architecture = load_state_file("designs/ARCHITECTURE.md")
    requirements = load_state_file("inputs/REQUIREMENTS.md")
    constraints = load_state_file("inputs/CONSTRAINTS.md")

    prompt_template = (get_prompts_dir() / "implement.txt").read_text()
    prompt = prompt_template.format(
        architecture=architecture,
        requirements=requirements,
        constraints=constraints,
    )

    provider = get_provider()
    p_hash = hash_prompt(prompt)
    implementation = provider.generate(prompt)

    output_path = "implementations/IMPLEMENTATION.md"
    save_state_file(output_path, implementation)

    trace(
        task="implement",
        inputs=["designs/ARCHITECTURE.md", "inputs/REQUIREMENTS.md", "inputs/CONSTRAINTS.md"],
        outputs=[output_path],
        model=provider.model,
        prompt_hash=p_hash,
    )
