from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import WorkflowModel, ExecutionModel
from app.schemas import ExecuteRequest, WorkflowExecutionResponse

router = APIRouter(tags=["Executions"])

def _run_steps(execution: ExecutionModel, workflow: WorkflowModel, db: Session):
    """Internal helper to execute steps sequentially and record audit logs."""
    current_data = execution.input_data
    step_results = []
    execution.status = "running"
    db.commit()

    try:
        steps = workflow.steps or []
        for index, step in enumerate(steps):
            step_name = step.get("name", f"Step {index + 1}")
            operation = step.get("operation")
            config = step.get("config", {})
            
            started_at = datetime.utcnow().isoformat()
            output = current_data
            step_error = None
            step_status = "success"

            try:
                if operation in ["uppercase", "text_upper"]:
                    if not isinstance(current_data, str):
                        current_data = str(current_data)
                    output = current_data.upper()
                
                elif operation in ["lowercase", "text_lower"]:
                    if not isinstance(current_data, str):
                        current_data = str(current_data)
                    output = current_data.lower()
                
                elif operation == "addition":
                    operand = config.get("operand", 0)
                    output = float(current_data) + float(operand)
  
                current_data = output

            except Exception as err:
                step_status = "failed"
                step_error = str(err)
                current_data = None
                
            completed_at = datetime.utcnow().isoformat()
            
            step_results.append({
                "step_index": index,
                "step_name": step_name,
                "operation": operation,
                "status": step_status,
                "input": execution.input_data if index == 0 else step_results[-1].get("output"),
                "output": output,
                "error": step_error,
                "started_at": started_at,
                "completed_at": completed_at
            })

            if step_status == "failed":
                raise Exception(step_error)

        execution.status = "completed"
        execution.output_data = current_data
        execution.step_results = step_results
        execution.completed_at = datetime.utcnow()

    except Exception as e:
        execution.status = "failed"
        execution.error_message = str(e)
        execution.step_results = step_results
        execution.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(execution)


@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
def execute_workflow(workflow_id: int, payload: ExecuteRequest, db: Session = Depends(get_db)):
    workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID {workflow_id} was not found."
        )
    
    new_execution = ExecutionModel(
        workflow_id=workflow_id,
        status="pending",
        input_data=payload.input_data,
        step_results=[],
        attempt=1,
        started_at=datetime.utcnow()
    )
    db.add(new_execution)
    db.commit()
    db.refresh(new_execution)

    _run_steps(new_execution, workflow, db)
    
    return new_execution


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
def get_execution(execution_id: int, db: Session = Depends(get_db)):
    execution = db.query(ExecutionModel).filter(ExecutionModel.id == execution_id).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution with ID {execution_id} was not found."
        )
        
    return execution


@router.post("/executions/{execution_id}/retry", response_model=WorkflowExecutionResponse)
def retry_execution(execution_id: int, db: Session = Depends(get_db)):
    execution = db.query(ExecutionModel).filter(ExecutionModel.id == execution_id).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution with ID {execution_id} was not found."
        )
        
    if execution.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry execution {execution_id} because its current status is '{execution.status}'. Only 'failed' executions can be retried."
        )
        
    execution.attempt += 1
    execution.status = "pending"
    execution.error_message = None
    db.commit()
    db.refresh(execution)
    
    workflow = db.query(WorkflowModel).filter(WorkflowModel.id == execution.workflow_id).first()
    if workflow:
        _run_steps(execution, workflow, db)
    
    return execution