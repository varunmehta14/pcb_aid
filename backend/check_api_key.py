#!/usr/bin/env python3
"""
Simple script to check if the API key is working with OpenRouter.
OpenRouter is a router/gateway service that works with multiple AI models.
"""
import os
import sys
from dotenv import load_dotenv

def check_openrouter_api():
    """Check if the API key is working with OpenRouter."""
    # Load environment variables
    load_dotenv()
    
    # Get the API key from environment or use hardcoded one
    api_key = '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'
    
    if not api_key:
        print("Error: API key not found")
        return False
    
    print(f"Using API key starting with: {api_key[:10]}...")
    
    try:
        # Try to import requests library
        try:
            import requests
        except ImportError:
            print("Installing requests package...")
            os.system("pip install requests")
            import requests
        
        # Set up the OpenRouter API request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # OpenRouter endpoint
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Request payload
        payload = {
            "model": "openai/gpt-3.5-turbo",  # OpenRouter format for model names
            "messages": [{"role": "user", "content": "Say hello"}],
            "max_tokens": 5
        }
        
        # Make the API call
        print("Testing the API key with OpenRouter...")
        response = requests.post(url, headers=headers, json=payload)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            print("Success! The API key is working with OpenRouter.")
            print(f"Response: {result['choices'][0]['message']['content']}")
            
            # Print available models
            print("\nFetching available models from OpenRouter...")
            models_response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
            if models_response.status_code == 200:
                models = models_response.json()['data']
                print(f"Available models ({len(models)}):")
                for i, model in enumerate(models[:5]):  # Show first 5 models
                    print(f"  {i+1}. {model['id']} - {model['name']}")
                if len(models) > 5:
                    print(f"  ... and {len(models) - 5} more")
            
            return True
        else:
            print(f"Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"Error: The API key is not working with OpenRouter: {str(e)}")
        return False

def main():
    """Main function to check API key with OpenRouter."""
    print("Checking if API key is working with OpenRouter...")
    
    is_working = check_openrouter_api()
    
    if not is_working:
        print("\nRecommendations:")
        print("1. Check if your OpenRouter API key is correct")
        print("2. Create an account at https://openrouter.ai if you don't have one")
        print("3. Get your API key from the OpenRouter dashboard")
        print("4. Make sure you have credits in your OpenRouter account")
    else:
        print("\nYour API key works with OpenRouter!")
        print("To use OpenRouter in your application:")
        print("1. Use the OpenRouter API endpoints instead of OpenAI")
        print("2. Set the Authorization header with your API key")
        print("3. Use 'openai/gpt-3.5-turbo' format for model names")
        print("\nFor more information, visit: https://openrouter.ai/docs")

if __name__ == "__main__":
    main() 