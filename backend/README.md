# PCB AiD - Backend

This is the FastAPI backend for the PCB AiD (Analyzer & Intelligent Design Assistant) application.

## Features

- PCB JSON file upload and processing
- Trace length calculations between pads
- Net listing and analysis
- API endpoints for frontend integration

## Setup & Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create uploads directory (will be created automatically on first run):
   ```bash
   mkdir uploads
   ```

## Running the Server

Start the development server:

```bash
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## API Endpoints

- `POST /upload_pcb`: Upload a PCB JSON file and initialize a session
- `GET /board/{board_id}/nets`: Get all nets in a PCB with component and pad counts
- `POST /board/{board_id}/calculate_trace`: Calculate trace length between two pads

## Development

- The backend integrates with the `trace_extractor.py` module for PCB analysis
- In-memory session storage is used for development (can be replaced with a database)
- The project structure is organized for easy extension with additional endpoints 