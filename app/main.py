from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine
from app.routes.executions import router as executions_router
from app.routes.workflows import router as workflows_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="WORKFLOW AUTOMATION API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(workflows_router)
app.include_router(executions_router)

@app.get("/", tags=["Health"])
def health_check():
    return {"message": "Workflow Automation API is running"}