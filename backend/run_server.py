"""
Simple server launcher script for testing.
"""

import uvicorn

if __name__ == "__main__":
    # Run the FastAPI app with uvicorn server
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    ) 