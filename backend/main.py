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

# Import our API key manager
from api_key_manager import require_valid_api_key
import api_routes

# Import the new board_routes with the safe analyzer
from api.board_routes import router as board_router

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

# Include our API routes
app.include_router(api_routes.router)

# Include our new board routes
app.include_router(board_router)

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

@app.get("/board/{board_id}/net/{net_name}/components")
async def get_net_components(board_id: str, net_name: str):
    """Get components connected to a specific net."""
    if board_id not in pcb_data_store:
        raise HTTPException(status_code=404, detail="PCB data not found")
    
    extractor = PCBTraceExtractor(pcb_data_store[board_id])
    components = extractor.get_components_by_net(net_name)
    
    if not components:
        # Return empty array instead of 404 to match frontend expectations
        return []
    
    return components

@app.post("/board/{board_id}/calculate_trace", response_model=TraceResponse)
async def calculate_trace(board_id: str, request: TraceRequest):
    """Calculate trace length between two pads."""
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
        raise HTTPException(status_code=404, detail="Trace not found")
    
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
    
    # Directly use the path_elements from get_trace_path if available
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

# Replace the existing analyze_pcb route with a fallback endpoint
# This is commented out because the new board_routes module provides this functionality
# 
# @app.post("/board/{board_id}/analyze")
# async def analyze_pcb(board_id: str, query: AIQuery, api_key: str = Depends(require_valid_api_key)):
#     """This route is now handled by board_routes module"""
#     raise HTTPException(status_code=410, detail="This endpoint has been moved to /board/{board_id}/analyze")

@app.get("/board/{board_id}/net/{net_name}/visualization")
async def get_net_visualization(board_id: str, net_name: str):
    """Get visualization data for a specific net."""
    if board_id not in pcb_data_store:
        raise HTTPException(status_code=404, detail="PCB data not found")
    
    extractor = PCBTraceExtractor(pcb_data_store[board_id])
    trace_details = extractor.get_trace_details(net_name)
    
    if not trace_details:
        raise HTTPException(status_code=404, detail=f"Net {net_name} not found or has no visualization data")
    
    # Convert raw trace details into visualization-friendly format
    # This transforms the data to match the format expected by the PCBVisualizer component
    visualization_data = {
        'net_name': net_name,
        'path_elements': []
    }
    
    # Add component connection information if available
    if 'connection_info' in trace_details and trace_details['connection_info']:
        connection = trace_details['connection_info']
        visualization_data.update({
            'start_component': connection.get('start_component', ''),
            'start_pad': connection.get('start_pad', ''),
            'end_component': connection.get('end_component', ''),
            'end_pad': connection.get('end_pad', ''),
            'length_mm': connection.get('length_mm', None)
        })
    
    # Add pads
    for pad in trace_details['pads']:
        visualization_data['path_elements'].append({
            'type': 'Pad',
            'component': pad['component'],
            'pad': pad['pad'],
            'location': [pad['x'], pad['y']],
            'layer': pad['layer']
        })
    
    # Add tracks and arcs (segments)
    for segment in trace_details['segments']:
        if segment['type'] == 'track':
            visualization_data['path_elements'].append({
                'type': 'Track',
                'start': [segment['start']['x'], segment['start']['y']],
                'end': [segment['end']['x'], segment['end']['y']],
                'layer': segment['layer'],
                'length': segment['length']
            })
        elif segment['type'] == 'arc':
            visualization_data['path_elements'].append({
                'type': 'Arc',
                'center': [segment['center']['x'], segment['center']['y']],
                'radius': segment['radius'],
                'start_angle': segment['start_angle'],
                'end_angle': segment['end_angle'],
                'start': [segment['start']['x'], segment['start']['y']],
                'end': [segment['end']['x'], segment['end']['y']],
                'layer': segment['layer'],
                'length': segment['length']
            })
    
    # Add vias
    for via in trace_details['vias']:
        visualization_data['path_elements'].append({
            'type': 'Via',
            'location': [via['x'], via['y']],
            'from_layer': via['from_layer'],
            'to_layer': via['to_layer'],
            'layer': f"{via['from_layer']}-{via['to_layer']}"  # Layer representation for vias
        })
    
    return visualization_data

@app.get("/board/{board_id}/net/{net_name}/critical_paths")
async def get_critical_paths(board_id: str, net_name: str):
    """Get critical path analysis for a specific net."""
    if board_id not in pcb_data_store:
        raise HTTPException(status_code=404, detail="PCB data not found")
    
    extractor = PCBTraceExtractor(pcb_data_store[board_id])
    critical_paths = extractor.get_critical_paths(net_name)
    
    if not critical_paths:
        raise HTTPException(status_code=404, detail=f"No critical path data found for net {net_name}")
    
    return critical_paths

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 