from typing import List
from fastapi import APIRouter, HTTPException, status

from backend.models.schemas import TaskCreateRequest, TaskResponse
from backend.services.task_service import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(request: TaskCreateRequest):
    """
    Create a new agentic task for industrial report analysis and approval note generation.
    """
    task = task_service.create_task(request)
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """
    Get task status, current execution phase, and execution trace.
    """
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found."
        )
    return task


@router.get("", response_model=List[TaskResponse])
async def list_tasks():
    """
    List all created tasks.
    """
    return task_service.list_tasks()
