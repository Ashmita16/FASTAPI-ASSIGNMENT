
import pytest

from app.schemas import OperationType
from app.services.operations import (
    OperationError,
    execute_operation,
)


def test_uppercase():
    result = execute_operation(
        OperationType.TEXT_UPPER, {}, "hello"
    )
    assert result == "HELLO"


def test_text_replace():
    result = execute_operation(
        OperationType.TEXT_REPLACE,
        {"old": "world", "new": "Python"},
        "hello world",
    )
    assert result == "hello Python"


def test_arithmetic():
    result = execute_operation(
        OperationType.ARITHMETIC,
        {"operator": "multiply", "operand": 3},
        5,
    )
    assert result == 15


def test_division_by_zero():
    with pytest.raises(OperationError):
        execute_operation(
            OperationType.ARITHMETIC,
            {"operator": "divide", "operand": 0},
            10,
        )
