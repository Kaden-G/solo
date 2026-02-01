"""Design task — LLM generates architecture from requirements."""

from prefect import task

from engine.context import get_prompts_dir, get_state_dir
from engine.decision_gates import DecisionRequired
from engine.llm_provider import get_provider
from engine.state_loader import decision_exists, load_state_file
from engine.tracer import hash_prompt, trace


@task(name="design")
def design_system() -> None:
    """Read requirements from state/inputs/, generate architecture via LLM."""
    requirements = load_state_file("inputs/REQUIREMENTS.md")
    constraints = load_state_file("inputs/CONSTRAINTS.md")
    non_goals = load_state_file("inputs/NON_GOALS.md")

    state_dir = get_state_dir()

    # Decision guard: if a prior run raised DecisionRequired, check that
    # the decision was recorded before re-running
    decision_key = "architecture_choice_needed"
    if (state_dir / "decisions" / f"{decision_key}.md").exists():
        decision_content = load_state_file(f"decisions/{decision_key}.md")
        # Extract choice from decision file
        for line in decision_content.splitlines():
            if line.startswith("Choice:"):
                chosen = line.split(":", 1)[1].strip()
                break
        else:
            chosen = ""
        extra_context = f"\n\nPrevious decision — chosen approach: {chosen}\n"
    else:
        extra_context = ""

    prompt_template = (get_prompts_dir() / "design.txt").read_text()
    prompt = prompt_template.format(
        requirements=requirements,
        constraints=constraints,
        non_goals=non_goals,
        extra_context=extra_context,
    )

    provider = get_provider()
    p_hash = hash_prompt(prompt)
    architecture = provider.generate(prompt)

    # If the LLM signals ambiguity, raise for human decision
    if "DECISION_REQUIRED:" in architecture:
        marker = architecture.split("DECISION_REQUIRED:")[1].strip()
        options = [opt.strip() for opt in marker.split("|") if opt.strip()]
        if not decision_exists("architecture_choice_needed"):
            raise DecisionRequired("Architecture choice needed", options)

    output_path = "designs/ARCHITECTURE.md"
    from engine.state_loader import save_state_file

    save_state_file(output_path, architecture)

    trace(
        task="design",
        inputs=["inputs/REQUIREMENTS.md", "inputs/CONSTRAINTS.md", "inputs/NON_GOALS.md"],
        outputs=[output_path],
        model=provider.model,
        prompt_hash=p_hash,
    )
