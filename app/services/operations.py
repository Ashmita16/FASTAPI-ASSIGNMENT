from typing import Any
from app.schemas import OperationType
from app.services.ai_service import classify_text


class OperationError(Exception):
    pass


def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and "value" in value:
        return _as_text(value["value"])
    return str(value)


def _as_number(value: Any) -> float | int:
    if isinstance(value, bool):
        raise OperationError("Boolean values are not valid numbers.")
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, dict) and "value" in value:
        return _as_number(value["value"])
    
    try:
        return float(value)
    except (TypeError, ValueError):
        raise OperationError(f"Cannot convert '{value}' to a number for arithmetic.")


def execute_operation(
    operation: OperationType,
    config: dict[str, Any],
    input_value: Any,
) -> Any:
    if operation == OperationType.UPPERCASE:
        return _as_text(input_value).upper()

    if operation == OperationType.LOWERCASE:
        return _as_text(input_value).lower()

    if operation == OperationType.REPLACE:
        old = config.get("old", "")
        new = config.get("new", "")
        return _as_text(input_value).replace(str(old), str(new))

    if operation == OperationType.PREFIX:
        prefix_text = config.get("text", "")
        return str(prefix_text) + _as_text(input_value)

    if operation == OperationType.SUFFIX:
        suffix_text = config.get("text", "")
        return _as_text(input_value) + str(suffix_text)

    if operation in [
        OperationType.ADDITION,
        OperationType.SUBTRACTION,
        OperationType.MULTIPLICATION,
        OperationType.DIVISION,
    ]:
        left = _as_number(input_value)
        right_raw = config.get("operand")
        
        if right_raw is None:
            raise OperationError(f"Arithmetic operation '{operation}' requires an 'operand' in config.")
        
        right = _as_number(right_raw)

        if operation == OperationType.ADDITION:
            return left + right
        if operation == OperationType.SUBTRACTION:
            return left - right
        if operation == OperationType.MULTIPLICATION:
            return left * right
        if operation == OperationType.DIVISION:
            if right == 0:
                raise OperationError("Division by zero is not allowed.")
            return left / right
    if operation == OperationType.AI_CLASSIFY:
        text = _as_text(input_value)
        categories = config.get("categories", ["positive", "negative"])
        return classify_text(text, categories)

    raise OperationError(f"Unsupported operation: {operation}")