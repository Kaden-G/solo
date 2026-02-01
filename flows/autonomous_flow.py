"""Main Prefect flow — THE entry point. Catches DecisionRequired exceptions."""

import logging

from prefect import flow

from engine.decision_gates import DecisionRequired, require_decision, save_decision
from engine.notifier import notify
from tasks.bootstrap import bootstrap_project
from tasks.design import design_system
from tasks.implement import implement_system
from tasks.test import test_system
from tasks.verify import verify_system

logger = logging.getLogger(__name__)


@flow(name="Autonomous Build Flow")
def autonomous_build() -> None:
    """Run the full autonomous build pipeline with human-in-the-loop gates."""

    # Step 1: Bootstrap — copy templates to state/inputs/
    logger.info("Starting bootstrap...")
    bootstrap_project()

    # Step 2: Design — LLM generates architecture
    logger.info("Starting design...")
    _run_with_gate(design_system)

    # Step 3: Implement — LLM generates code from design
    logger.info("Starting implementation...")
    implement_system()

    # Step 4: Test — validate implementation
    logger.info("Starting tests...")
    test_system()

    # Step 5: Verify — check acceptance criteria
    logger.info("Starting verification...")
    verify_system()

    notify("Autonomous build flow completed.")
    logger.info("Flow completed successfully.")


def _run_with_gate(task_fn) -> None:
    """Run a task, catch DecisionRequired, pause for human input, then re-run."""
    try:
        task_fn()
    except DecisionRequired as e:
        logger.info("Decision required: %s (options: %s)", e.summary, e.options)
        notify(f"Decision required: {e.summary}")

        choice = require_decision(e.summary, e.options)
        logger.info("Decision received: %s -> %s", e.summary, choice)

        save_decision(e.summary, choice)
        task_fn()  # Re-run with decision now available in state/decisions/


if __name__ == "__main__":
    autonomous_build()
