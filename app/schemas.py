from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class OperationType(str, Enum):
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    REPLACE = "replace"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"
    AI_CLASSIFY = "ai_classify"


class StepDefinition(BaseModel):
    name: str
    operation: OperationType
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration parameters depending on the operation (e.g., {'operand': 5} for addition, {} for uppercase)"
    )


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str = ""
    steps: list[StepDefinition] = Field(min_length=1, max_length=50)


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    steps: list[StepDefinition] | None = Field(default=None, min_length=1, max_length=50)


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    steps: list[dict[str, Any]]


class ExecuteRequest(BaseModel):
    input_data: Any


class WorkflowExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    status: str
    input_data: Any
    output_data: Any | None
    step_results: list[dict[str, Any]]
    attempt: int
    error_message: str | None
    started_at: Any
    completed_at: Any


class WorkflowGenerateRequest(BaseModel):
    description: str = Field(min_length=5, max_length=5000)