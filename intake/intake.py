"""Intake CLI — collect, validate, normalize project specs before engine execution."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from intake.renderer import render_all
from intake.schema import (
    AutonomyLevel,
    Constraints,
    DecisionAuthority,
    DeliveryFormat,
    Domain,
    Execution,
    LLMProvider,
    Notifications,
    NotificationMethod,
    Outputs,
    ProjectInfo,
    ProjectSpec,
    Requirements,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _prompt(label: str, required: bool = True, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    suffix += " (required)" if required and not default else ""
    while True:
        value = input(f"  {label}{suffix}: ").strip()
        if not value and default:
            return default
        if not value and required:
            print("    ↳ This field is required.")
            continue
        return value


def _prompt_list(label: str, min_items: int = 0) -> list[str]:
    print(f"  {label} (one per line, empty line to finish):")
    items = []
    while True:
        value = input("    - ").strip()
        if not value:
            if len(items) < min_items:
                print(f"    ↳ At least {min_items} item(s) required.")
                continue
            break
        items.append(value)
    return items


def _prompt_choice(label: str, choices: list[str], default: str = "") -> str:
    options = " / ".join(choices)
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"  {label} ({options}){suffix}: ").strip().lower()
        if not value and default:
            return default
        if value in [c.lower() for c in choices]:
            return value
        print(f"    ↳ Choose one of: {options}")


def _prompt_yn(label: str, default: bool = False) -> bool:
    d = "Y/n" if default else "y/N"
    value = input(f"  {label} [{d}]: ").strip().lower()
    if not value:
        return default
    return value in ("y", "yes")


def collect_interactive() -> ProjectSpec:
    """Walk the user through every required field. Block on missing info."""
    print("\n═══ Autonomy Engine — Project Intake ═══\n")

    # --- Project ---
    print("▸ Project")
    name = _prompt("Name")
    description = _prompt("Description (what does it do)")
    domain = _prompt_choice("Domain", ["software", "data", "ml", "infra"], "software")

    # --- Requirements ---
    print("\n▸ Functional Requirements")
    functional = _prompt_list("List each requirement", min_items=1)

    print("\n▸ Non-Functional Requirements (optional)")
    non_functional = _prompt_list("List each requirement")

    # --- Constraints ---
    print("\n▸ Constraints")
    tech_stack = _prompt_list("Tech stack (languages, frameworks, platforms)")
    performance = _prompt("Performance constraints", required=False) or None
    security = _prompt("Security constraints", required=(domain == "infra")) or None

    # --- Non-Goals ---
    print("\n▸ Non-Goals (what this project will NOT do)")
    non_goals = _prompt_list("List each non-goal")

    # --- Acceptance Criteria ---
    print("\n▸ Acceptance Criteria")
    acceptance = _prompt_list("List each testable criterion", min_items=1)

    # --- Execution ---
    print("\n▸ Execution Settings")
    autonomy = _prompt_choice("Autonomy level", ["full", "gated"], "gated")
    authority = _prompt_choice("Decision authority", ["human", "engine"], "human")
    provider = _prompt_choice("LLM provider", ["claude", "openai"], "claude")

    # --- Outputs ---
    print("\n▸ Expected Outputs")
    artifacts = _prompt_list("Expected artifacts", min_items=1)
    delivery = _prompt_choice("Delivery format", ["repo", "docs", "cli"], "repo")

    # --- Notifications ---
    print("\n▸ Notifications")
    notif_enabled = _prompt_yn("Enable notifications", default=False)
    notif_method = "none"
    if notif_enabled:
        notif_method = _prompt_choice("Method", ["slack", "email"], "slack")

    spec = ProjectSpec(
        project=ProjectInfo(name=name, description=description, domain=Domain(domain)),
        requirements=Requirements(functional=functional, non_functional=non_functional),
        constraints=Constraints(tech_stack=tech_stack, performance=performance, security=security),
        non_goals=non_goals,
        acceptance_criteria=acceptance,
        execution=Execution(
            autonomy_level=AutonomyLevel(autonomy),
            decision_authority=DecisionAuthority(authority),
            llm_provider=LLMProvider(provider),
        ),
        outputs=Outputs(
            expected_artifacts=artifacts,
            delivery_format=DeliveryFormat(delivery),
        ),
        notifications=Notifications(
            enabled=notif_enabled,
            method=NotificationMethod(notif_method),
        ),
    )

    return spec


def load_from_file(path: str) -> ProjectSpec:
    """Load and validate a project spec from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return ProjectSpec(**data)


def confirm_spec(spec: ProjectSpec) -> bool:
    """Print the spec summary and ask for confirmation."""
    print("\n═══ Project Spec Summary ═══\n")
    print(f"  Project:      {spec.project.name}")
    print(f"  Domain:       {spec.project.domain.value}")
    print(f"  Description:  {spec.project.description}")
    print(f"  Requirements: {len(spec.requirements.functional)} functional, "
          f"{len(spec.requirements.non_functional)} non-functional")
    print(f"  Constraints:  {len(spec.constraints.tech_stack)} tech stack items")
    print(f"  Non-Goals:    {len(spec.non_goals)} items")
    print(f"  Acceptance:   {len(spec.acceptance_criteria)} criteria")
    print(f"  Autonomy:     {spec.execution.autonomy_level.value}")
    print(f"  Authority:    {spec.execution.decision_authority.value}")
    print(f"  LLM:          {spec.execution.llm_provider.value}")
    print(f"  Artifacts:    {', '.join(spec.outputs.expected_artifacts)}")
    print(f"  Delivery:     {spec.outputs.delivery_format.value}")
    print()
    return _prompt_yn("Confirm and write to state/inputs/", default=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="intake",
        description="Autonomy Engine — Project Intake & Normalization",
    )
    sub = parser.add_subparsers(dest="command")

    # intake new-project (interactive)
    sub.add_parser("new-project", help="Create a new project spec interactively")

    # intake from-file (load YAML)
    from_file = sub.add_parser("from-file", help="Load a project spec from a YAML file")
    from_file.add_argument("path", help="Path to project_spec.yml")

    # intake validate (check existing spec)
    validate = sub.add_parser("validate", help="Validate an existing project_spec.yml")
    validate.add_argument("path", help="Path to project_spec.yml")

    args = parser.parse_args()

    if args.command == "new-project":
        try:
            spec = collect_interactive()
        except (KeyboardInterrupt, EOFError):
            print("\n\nIntake cancelled.")
            sys.exit(1)

        if not confirm_spec(spec):
            print("Aborted.")
            sys.exit(1)

        written = render_all(spec)
        print(f"\nIntake complete. Wrote {len(written)} files to state/inputs/:")
        for path in written:
            print(f"  ✓ {path}")
        print("\nEngine is ready to run.")

    elif args.command == "from-file":
        try:
            spec = load_from_file(args.path)
        except ValidationError as e:
            print(f"Validation failed:\n{e}")
            sys.exit(1)

        print(f"Spec loaded from {args.path}")
        if not confirm_spec(spec):
            print("Aborted.")
            sys.exit(1)

        written = render_all(spec)
        print(f"\nIntake complete. Wrote {len(written)} files to state/inputs/:")
        for path in written:
            print(f"  ✓ {path}")

    elif args.command == "validate":
        try:
            spec = load_from_file(args.path)
            print(f"Valid. Project: {spec.project.name}")
        except ValidationError as e:
            print(f"Invalid:\n{e}")
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
