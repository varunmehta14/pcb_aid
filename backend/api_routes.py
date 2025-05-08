"""
API routes for OpenRouter key validation and management.
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Optional
from pydantic import BaseModel

from api_key_manager import validate_key, ApiKeyStatus

# Create router
router = APIRouter(
    prefix="/api/keys",
    tags=["API Keys"],
)

class ApiKeyRequest(BaseModel):
    """Request model for API key validation"""
    api_key: str

@router.get("/validate", response_model=ApiKeyStatus)
async def validate_api_key() -> ApiKeyStatus:
    """
    Validate the currently configured API key.
    
    Returns:
        ApiKeyStatus with validation results and available models
    """
    return validate_key()

@router.post("/validate", response_model=ApiKeyStatus)
async def validate_provided_key(request: ApiKeyRequest) -> ApiKeyStatus:
    """
    Validate a provided API key.
    
    Args:
        request: The request containing the API key to validate
        
    Returns:
        ApiKeyStatus with validation results and available models
    """
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    return validate_key(request.api_key)

@router.get("/models")
async def get_models() -> Dict:
    """
    Get available models using the configured API key.
    
    Returns:
        Dict containing the list of available models or an error message
    """
    status = validate_key()
    
    if not status.is_valid:
        raise HTTPException(status_code=401, detail=status.message)
    
    return {"models": status.available_models} 