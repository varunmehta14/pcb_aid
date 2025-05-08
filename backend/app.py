"""
Main FastAPI application for PCB AiD backend.
"""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import traceback
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

# Import our modules
from api_routes import router as api_router
from api_key_manager import require_valid_api_key

# Initialize FastAPI app
app = FastAPI(
    title="PCB AiD API",
    description="API for PCB AiD (Analyzer & Intelligent Design Assistant)",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    # Log the error
    print(f"Unhandled exception: {str(exc)}")
    print(traceback.format_exc())
    
    # Return a generic error response
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred", "error": str(exc)},
    )

# Include our routers
app.include_router(api_router)

# Add additional routers for PCB analysis as needed

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "status": "online", 
        "name": "PCB AiD API",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if API key is available
    api_key = os.getenv("OPENROUTER_API_KEY")
    return {
        "status": "healthy",
        "api_key_available": api_key is not None,
    }

if __name__ == "__main__":
    import uvicorn
    # Run the app with uvicorn when script is executed directly
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 