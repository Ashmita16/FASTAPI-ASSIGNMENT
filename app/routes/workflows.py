from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import WorkflowModel
from app.schemas import WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowGenerateRequest
from app.services.ai_service import generate_workflow

router = APIRouter(prefix="/workflows", tags=["Workflows"])

@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)):
    new_workflow = WorkflowModel(
        name=payload.name,
        description=payload.description,
        steps=[step.model_dump() for step in payload.steps]
    )
    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)
    return new_workflow

@router.get("/", response_model=list[WorkflowResponse])
def list_workflows(db: Session = Depends(get_db)):
    return db.query(WorkflowModel).all()

@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID {workflow_id} was not found."
        )
    return workflow

@router.post("/generate", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def generate_workflow_endpoint(payload: WorkflowGenerateRequest, db: Session = Depends(get_db)):
    try:
        generated_data = generate_workflow(payload.description)
     
        if isinstance(generated_data, str):
            import json
            data = json.loads(generated_data)
        elif hasattr(generated_data, "model_dump"):
            data = generated_data.model_dump()
        else:
            data = generated_data

        new_workflow = WorkflowModel(
            name=data.get("name", "AI Generated Workflow"),
            description=data.get("description", payload.description),
            steps=data.get("steps", [])
        )
        db.add(new_workflow)
        db.commit()
        db.refresh(new_workflow)
        
        return new_workflow
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )