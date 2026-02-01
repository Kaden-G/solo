"""Project spec schema — the single authoritative contract for every engine run."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Domain(str, Enum):
    SOFTWARE = "software"
    DATA = "data"
    ML = "ml"
    INFRA = "infra"


class AutonomyLevel(str, Enum):
    FULL = "full"
    GATED = "gated"


class DecisionAuthority(str, Enum):
    HUMAN = "human"
    ENGINE = "engine"


class LLMProvider(str, Enum):
    CLAUDE = "claude"
    OPENAI = "openai"


class DeliveryFormat(str, Enum):
    REPO = "repo"
    DOCS = "docs"
    CLI = "cli"


class NotificationMethod(str, Enum):
    SLACK = "slack"
    EMAIL = "email"
    NONE = "none"


class ProjectInfo(BaseModel):
    name: str = Field(min_length=1, description="Project name")
    description: str = Field(min_length=10, description="What the project does")
    domain: Domain


class Requirements(BaseModel):
    functional: list[str] = Field(min_length=1, description="At least one functional requirement")
    non_functional: list[str] = Field(default_factory=list)


class Constraints(BaseModel):
    tech_stack: list[str] = Field(default_factory=list)
    performance: str | None = None
    security: str | None = None


class Execution(BaseModel):
    autonomy_level: AutonomyLevel = AutonomyLevel.GATED
    decision_authority: DecisionAuthority = DecisionAuthority.HUMAN
    llm_provider: LLMProvider = LLMProvider.CLAUDE


class Outputs(BaseModel):
    expected_artifacts: list[str] = Field(min_length=1, description="At least one expected artifact")
    delivery_format: DeliveryFormat = DeliveryFormat.REPO


class Notifications(BaseModel):
    enabled: bool = False
    method: NotificationMethod = NotificationMethod.NONE


class ProjectSpec(BaseModel):
    """Root schema — everything the engine needs to run."""

    project: ProjectInfo
    requirements: Requirements
    constraints: Constraints = Field(default_factory=Constraints)
    non_goals: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(
        min_length=1, description="At least one acceptance criterion"
    )
    execution: Execution = Field(default_factory=Execution)
    outputs: Outputs
    notifications: Notifications = Field(default_factory=Notifications)

    @model_validator(mode="after")
    def security_constraints_required_if_security_domain(self) -> ProjectSpec:
        """Block if domain touches security but no security constraints provided."""
        if self.project.domain == Domain.INFRA and not self.constraints.security:
            raise ValueError(
                "Security constraints are required for infra-domain projects. "
                "Set constraints.security to describe your security requirements."
            )
        return self
