"""
Utility functions for the AI functionality.
"""
import requests
from typing import Optional, Dict, Any, Tuple, List
from .config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

def validate_openrouter_api_key(api_key: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validate the OpenRouter API key by making a test request.
    
    Args:
        api_key: Optional API key to validate. If None, uses the key from config.
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Use provided key or fall back to configured key
    key_to_validate = api_key or OPENROUTER_API_KEY
    
    if not key_to_validate:
        return False, "No API key provided"
    
    try:
        # Set up the OpenRouter API request
        headers = {
            "Authorization": f"Bearer {key_to_validate}",
            "Content-Type": "application/json"
        }
        
        # OpenRouter endpoint for completions
        url = f"{OPENROUTER_BASE_URL}/chat/completions"
        
        # Simple test payload
        payload = {
            "model": "mistralai/mistral-7b-instruct:free",  # Use free tier model for validation
            "messages": [{"role": "user", "content": "Test connection"}],
            "max_tokens": 5
        }
        
        # Make the API call with a timeout
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        # Check response
        if response.status_code == 200:
            return True, "API key is valid"
        else:
            return False, f"API validation failed with status {response.status_code}: {response.text}"
        
    except requests.exceptions.Timeout:
        return False, "API request timed out"
    except requests.exceptions.RequestException as e:
        return False, f"API request failed: {str(e)}"
    except Exception as e:
        return False, f"API validation error: {str(e)}"

def get_available_models(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get the list of available models from OpenRouter.
    
    Args:
        api_key: Optional API key to use. If None, uses the key from config.
        
    Returns:
        List of model information dictionaries
    """
    # Use provided key or fall back to configured key
    key_to_use = api_key or OPENROUTER_API_KEY
    
    if not key_to_use:
        return []
    
    try:
        # Set up the OpenRouter API request
        headers = {
            "Authorization": f"Bearer {key_to_use}",
            "Content-Type": "application/json"
        }
        
        # OpenRouter endpoint for models
        url = f"{OPENROUTER_BASE_URL}/models"
        
        # Make the API call with a timeout
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check response
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f"Failed to get models: {response.status_code}, {response.text}")
            return []
        
    except Exception as e:
        print(f"Error getting models: {str(e)}")
        return [] 