"""
API routes for PCB board analysis and operations.
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Optional
from pydantic import BaseModel
import os
import json
from ai.safe_analyzer import SafePCBAnalyzer

# Create router
router = APIRouter(
    prefix="/board",
    tags=["Board Analysis"],
)

class QueryModel(BaseModel):
    """Request model for PCB analysis query"""
    query: str

@router.post("/{board_id}/analyze")
async def analyze_pcb(board_id: str, request: QueryModel) -> Dict:
    """
    Analyze a PCB design based on a natural language query.
    
    Args:
        board_id: Identifier for the PCB board
        request: The request containing the query to analyze
        
    Returns:
        Dict containing the analysis result
    """
    try:
        # In a real application, this would load the PCB data for the specific board_id
        # For now, we'll use the sample PCB data
        try:
            with open('test_data/sample_pcb.json', 'r') as f:
                pcb_data = json.load(f)
        except Exception as e:
            raise HTTPException(
                status_code=404, 
                detail=f"PCB data for board ID {board_id} not found: {str(e)}"
            )
        
        # Get API key from environment
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Create the safe analyzer
        analyzer = SafePCBAnalyzer(pcb_data, api_key)
        
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