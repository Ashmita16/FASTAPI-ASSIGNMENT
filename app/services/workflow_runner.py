from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import WorkflowExecution
from app.services.operations import execute_operation, OperationError


def current_time() -> datetime:
    return datetime.now(timezone.utc)


def run_workflow_execution(db: Session, execution_id: int) -> None:
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    if not execution:
        return

    workflow = execution.workflow
    if not workflow:
        execution.status = "failed"
        execution.error_message = "Associated workflow not found."
        db.commit()
        return
    execution.status = "running"
    execution.started_at = current_time()
    execution.error_message = None
    db.commit()

    current_input = execution.input_data
    step_results = []

    try:
        for idx, step in enumerate(workflow.steps):
            step_name = step.get(f"name", f"Step {idx + 1}")
            operation_type = step.get("operation")
            config = step.get("config", {})

            step_start_time = current_time()
            try:
                output = execute_operation(operation_type, config, current_input)
                
                step_results.append({
                    "step_index": idx,
                    "step_name": step_name,
                    "operation": operation_type,
                    "status": "success",
                    "input": current_input,
                    "output": output,
                    "started_at": step_start_time.isoformat(),
                    "completed_at": current_time().isoformat(),
                })
                current_input = output
            except (OperationError, Exception) as exc:
                step_results.append({
                    "step_index": idx,
                    "step_name": step_name,
                    "operation": operation_type,
                    "status": "failed",
                    "input": current_input,
                    "error": str(exc),
                    "started_at": step_start_time.isoformat(),
                    "completed_at": current_time().isoformat(),
                })
                raise exc

        execution.status = "completed"
        execution.output_data = {"result": current_input}
        execution.step_results = step_results
        execution.completed_at = current_time()
        db.commit()

    except Exception as exc:
        execution.status = "failed"
        execution.error_message = str(exc)
        execution.step_results = step_results
        execution.completed_at = current_time()
        db.commit()


def retry_workflow_execution(db: Session, execution_id: int) -> WorkflowExecution:
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    if not execution:
        raise ValueError("Execution not found.")
    
    if execution.status != "failed":
        raise ValueError("Only failed executions can be retried.")

    execution.attempt += 1
    execution.status = "pending"
    db.commit()

    run_workflow_execution(db, execution.id)
    
    db.refresh(execution)
    return execution