"""
API routes for PCB board analysis and operations.
"""
from fastapi import APIRouter, HTTPException, Body, Depends, BackgroundTasks
from typing import Dict, Optional, Any
from pydantic import BaseModel
import os
import json
import time
import asyncio
from ai.safe_analyzer import SafePCBAnalyzer

# Import dependencies
from dependencies import get_pcb_data_store

# Create router
router = APIRouter(
    prefix="/board",
    tags=["Board Analysis"],
)

# Store active analysis tasks to allow cancellation
active_tasks: Dict[str, Dict[str, Any]] = {}

class QueryModel(BaseModel):
    """Request model for PCB analysis query"""
    query: str

class TaskStatusModel(BaseModel):
    """Response model for task status"""
    task_id: str
    status: str
    message: Optional[str] = None

@router.post("/{board_id}/analyze")
async def analyze_pcb(board_id: str, request: QueryModel, background_tasks: BackgroundTasks, pcb_data_store: Dict = Depends(get_pcb_data_store)) -> Dict:
    """
    Analyze a PCB design based on a natural language query.
    
    Args:
        board_id: Identifier for the PCB board
        request: The request containing the query to analyze
        background_tasks: FastAPI background tasks
        pcb_data_store: Dictionary containing all PCB data, injected as a dependency
        
    Returns:
        Dict containing the analysis result
    """
    try:
        # Check if the board_id exists in the pcb_data_store
        if board_id not in pcb_data_store:
            # For testing/sample purposes, try to load from test_data if not found in store
            try:
                with open('test_data/sample_pcb.json', 'r') as f:
                    pcb_data = json.load(f)
                    print(f"Using test_data/sample_pcb.json for board_id {board_id}")
            except Exception as e:
                raise HTTPException(
                    status_code=404, 
                    detail=f"PCB data for board ID {board_id} not found: {str(e)}"
                )
        else:
            # Use the actual PCB data from the store
            pcb_data = pcb_data_store[board_id]
            print(f"Using stored PCB data for board_id {board_id}")
        
        # Get API key from environment
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Create the safe analyzer with a 45-second timeout
        analyzer = SafePCBAnalyzer(pcb_data, api_key, timeout=45)
        
        # Process the query
        result = analyzer.process_query(request.query)
        
        return {"result": result}
    
    except Exception as e:
        # Return a more graceful error message
        return {
            "error": str(e),
            "message": "Failed to analyze PCB. The analyzer encountered an error.",
            "result": "Please try a more specific query or contact support if the issue persists."
        }

@router.post("/{board_id}/analyze/async")
async def analyze_pcb_async(board_id: str, request: QueryModel, background_tasks: BackgroundTasks, pcb_data_store: Dict = Depends(get_pcb_data_store)) -> TaskStatusModel:
    """
    Start an asynchronous PCB analysis operation.
    
    Args:
        board_id: Identifier for the PCB board
        request: The request containing the query to analyze
        background_tasks: FastAPI background tasks
        pcb_data_store: Dictionary containing all PCB data, injected as a dependency
        
    Returns:
        TaskStatusModel with the task ID for checking status
    """
    # Generate a unique task ID
    task_id = f"{board_id}_{int(time.time())}"
    
    # Set initial task status
    active_tasks[task_id] = {
        "status": "pending",
        "board_id": board_id,
        "query": request.query,
        "result": None,
        "error": None,
        "start_time": time.time()
    }
    
    # Add the background task
    background_tasks.add_task(
        process_analysis_task, 
        task_id=task_id, 
        board_id=board_id, 
        query=request.query, 
        pcb_data_store=pcb_data_store
    )
    
    return TaskStatusModel(
        task_id=task_id,
        status="pending",
        message="Analysis task started"
    )

@router.get("/analyze/task/{task_id}")
async def get_task_status(task_id: str) -> Dict:
    """
    Get the status of an asynchronous analysis task.
    
    Args:
        task_id: The ID of the task to check
        
    Returns:
        Dict containing the task status and result if available
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail=f"Task ID {task_id} not found")
    
    task = active_tasks[task_id]
    
    response = {
        "task_id": task_id,
        "status": task["status"],
        "elapsed_time": round(time.time() - task["start_time"], 2)
    }
    
    if task["status"] == "completed":
        response["result"] = task["result"]
    elif task["status"] == "error":
        response["error"] = task["error"]
    
    return response

@router.delete("/analyze/task/{task_id}")
async def cancel_task(task_id: str) -> Dict:
    """
    Cancel an ongoing analysis task.
    
    Args:
        task_id: The ID of the task to cancel
        
    Returns:
        Dict with confirmation of cancellation
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail=f"Task ID {task_id} not found")
    
    task = active_tasks[task_id]
    
    if task["status"] in ["completed", "error", "cancelled"]:
        return {
            "task_id": task_id,
            "status": task["status"],
            "message": f"Task already in {task['status']} state"
        }
    
    # Mark task as cancelled
    task["status"] = "cancelled"
    task["error"] = "Task cancelled by user"
    
    return {
        "task_id": task_id,
        "status": "cancelled",
        "message": "Task has been cancelled"
    }

# Background task processing function
async def process_analysis_task(task_id: str, board_id: str, query: str, pcb_data_store: Dict):
    """Process an analysis task in the background."""
    try:
        # Update task status
        active_tasks[task_id]["status"] = "running"
        
        # Check if the board_id exists in the pcb_data_store
        if board_id not in pcb_data_store:
            # For testing/sample purposes, try to load from test_data if not found in store
            try:
                with open('test_data/sample_pcb.json', 'r') as f:
                    pcb_data = json.load(f)
                    print(f"Using test_data/sample_pcb.json for board_id {board_id}")
            except Exception as e:
                active_tasks[task_id]["status"] = "error"
                active_tasks[task_id]["error"] = f"PCB data for board ID {board_id} not found: {str(e)}"
                return
        else:
            # Use the actual PCB data from the store
            pcb_data = pcb_data_store[board_id]
            print(f"Using stored PCB data for board_id {board_id}")
        
        # Check if task has been cancelled
        if active_tasks[task_id]["status"] == "cancelled":
            return
        
        # Get API key from environment
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Create the safe analyzer with a longer timeout for background tasks
        analyzer = SafePCBAnalyzer(pcb_data, api_key, timeout=60)
        
        # Process the query
        result = analyzer.process_query(query)
        
        # Check if task has been cancelled
        if active_tasks[task_id]["status"] == "cancelled":
            return
        
        # Update task with the result
        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["result"] = result
    
    except Exception as e:
        # Update task with the error
        active_tasks[task_id]["status"] = "error"
        active_tasks[task_id]["error"] = str(e)
        print(f"Error processing task {task_id}: {str(e)}")
        
    finally:
        # Schedule task cleanup after 1 hour
        asyncio.create_task(cleanup_task(task_id, 3600))

async def cleanup_task(task_id: str, delay_seconds: int):
    """Clean up a task after a delay."""
    await asyncio.sleep(delay_seconds)
    if task_id in active_tasks:
        del active_tasks[task_id]
        print(f"Cleaned up task {task_id}") 