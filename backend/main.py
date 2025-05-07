from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import os
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from trace_extractor import PCBTraceExtractor
from ai.workflow import PCBWorkflow

# Import the trace extractor
import sys
sys.path.append('..')  # Add parent directory to path for importing trace_extractor

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="PCB AiD API",
    description="API for PCB Analysis and Intelligent Design Assistant",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store PCB data in memory (in production, use a proper database)
pcb_data_store: Dict[str, dict] = {}

# Pydantic models
from pydantic import BaseModel

class UploadResponse(BaseModel):
    session_id: str
    filename: str
    message: str

class NetInfo(BaseModel):
    net_name: str
    component_count: int
    pad_count: int

class TraceRequest(BaseModel):
    net_name: str
    start_component: str
    start_pad: str
    end_component: str
    end_pad: str

class TraceResponse(BaseModel):
    net_name: str
    start_component: str
    start_pad: str
    end_component: str
    end_pad: str
    length_mm: Optional[float] = None
    path_description: Optional[str] = None
    path_elements: Optional[List[Dict[str, Any]]] = None

class AIQuery(BaseModel):
    query: str

@app.get("/")
async def root():
    return {"message": "Welcome to PCB AiD API"}

@app.post("/upload_pcb", response_model=UploadResponse)
async def upload_pcb(file: UploadFile = File(...)):
    """Upload a PCB JSON file and store it in memory."""
    try:
        # Read and parse the JSON file
        content = await file.read()
        pcb_data = json.loads(content)
        
        # Create a unique session ID
        session_id = str(uuid.uuid4())
        
        # Store the PCB data
        pcb_data_store[session_id] = pcb_data
        
        return UploadResponse(
            session_id=session_id,
            filename=file.filename,
            message="PCB file uploaded successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/board/{board_id}/nets", response_model=List[NetInfo])
async def get_nets(board_id: str):
    """Get the list of nets in the PCB."""
    if board_id not in pcb_data_store:
        raise HTTPException(status_code=404, detail="PCB data not found")
    
    extractor = PCBTraceExtractor(pcb_data_store[board_id])
    return extractor.get_nets()

@app.post("/board/{board_id}/calculate_trace", response_model=TraceResponse)
async def calculate_trace(board_id: str, request: TraceRequest):
    """Calculate trace length between two pads."""
    if board_id not in pcb_data_store:
        raise HTTPException(status_code=404, detail="PCB data not found")
    
    extractor = PCBTraceExtractor(pcb_data_store[board_id])
    length = extractor.extract_traces_between_pads(
        request.start_component,
        request.start_pad,
        request.end_component,
        request.end_pad
    )
    
    if length is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    
    return TraceResponse(
        net_name=request.net_name,
        start_component=request.start_component,
        start_pad=request.start_pad,
        end_component=request.end_component,
        end_pad=request.end_pad,
        length_mm=length  # Already in mm from extract_traces_between_pads
    )

@app.post("/board/{board_id}/trace_path", response_model=TraceResponse)
async def get_trace_path(board_id: str, request: TraceRequest):
    """Get detailed trace path information between two pads."""
    if board_id not in pcb_data_store:
        raise HTTPException(status_code=404, detail="PCB data not found")
    
    extractor = PCBTraceExtractor(pcb_data_store[board_id])
    path_info = extractor.get_trace_path(
        request.start_component,
        request.start_pad,
        request.end_component,
        request.end_pad
    )
    
    if not path_info['path_exists']:
        raise HTTPException(status_code=404, detail="Trace path not found")
    
    return TraceResponse(
        net_name=request.net_name,
        start_component=request.start_component,
        start_pad=request.start_pad,
        end_component=request.end_component,
        end_pad=request.end_pad,
        length_mm=path_info['length_mm'],
        path_description=path_info['path_description'],
        path_elements=path_info['path_elements']
    )

@app.post("/board/{board_id}/analyze")
async def analyze_pcb(board_id: str, query: AIQuery):
    """Analyze the PCB using AI agents."""
    if board_id not in pcb_data_store:
        raise HTTPException(status_code=404, detail="PCB data not found")
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured"
        )
    
    # Create and run the AI workflow
    workflow = PCBWorkflow(pcb_data_store[board_id], openai_api_key)
    response = workflow.process_query(query.query)
    
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 