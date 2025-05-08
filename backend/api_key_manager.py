"""
API Key management functionality for the backend.
"""
import os
from typing import Dict, Optional, Any, Tuple, List
from dotenv import load_dotenv
from fastapi import HTTPException
from pydantic import BaseModel

# Import validation utilities
from ai.utils import validate_openrouter_api_key, get_available_models

# Load environment variables
load_dotenv()

class ApiKeyStatus(BaseModel):
    """Pydantic model for API key status response"""
    is_valid: bool
    message: str
    available_models: List[Dict[str, Any]] = []

def get_api_key() -> Optional[str]:
    """Get the OpenRouter API key from environment variables"""
    return os.getenv("OPENROUTER_API_KEY")

def validate_key(api_key: Optional[str] = None) -> ApiKeyStatus:
    """
    Validate the API key and return information about its status
    
    Args:
        api_key: The API key to validate. If None, uses the key from environment.
        
    Returns:
        ApiKeyStatus object with validation results and available models
    """
    # Get key from parameter or environment
    key_to_validate = api_key or get_api_key()
    
    if not key_to_validate:
        return ApiKeyStatus(
            is_valid=False,
            message="No API key available. Please set OPENROUTER_API_KEY environment variable."
        )
    
    # Validate the key
    is_valid, message = validate_openrouter_api_key(key_to_validate)
    
    # If valid, get available models
    available_models = []
    if is_valid:
        available_models = get_available_models(key_to_validate)
    
    return ApiKeyStatus(
        is_valid=is_valid,
        message=message,
        available_models=available_models
    )

def require_valid_api_key(api_key: Optional[str] = None) -> str:
    """
    Ensure a valid API key is available or raise an appropriate exception.
    
    Args:
        api_key: Optional API key to use. If None, uses the key from environment.
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: If the API key is missing or invalid
    """
    # Get key from parameter or environment
    key = api_key or get_api_key()
    
    if not key:
        raise HTTPException(
            status_code=401,
            detail="API key missing. Please set OPENROUTER_API_KEY environment variable."
        )
    
    # Validate the key
    is_valid, message = validate_openrouter_api_key(key)
    
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid API key: {message}"
        )
    
    return key 