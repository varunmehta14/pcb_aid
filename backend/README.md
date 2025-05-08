# PCB AiD - Backend

This is the FastAPI backend for the PCB AiD (Analyzer & Intelligent Design Assistant) application.

## Features

- PCB JSON file upload and processing
- Trace length calculations between pads
- Net listing and analysis
- API endpoints for frontend integration
- AI-powered PCB analysis using OpenRouter

## Setup & Installation

1. Clone and navigate to the repository:
   ```bash
   git clone <repository-url>
   cd pcb_aid/backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your OpenRouter API key:
   ```bash
   python setup_env.py
   ```
   Follow the prompts to enter your OpenRouter API key. Alternatively, you can manually create a `.env` file with:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```

5. Test your OpenRouter API key:
   ```bash
   python test_openrouter.py
   ```

## Running the Server

The simplest way to start the server is using the provided script:

```bash
./run_server.sh
```

This script will:
1. Check for and create a virtual environment if needed
2. Install dependencies
3. Verify the OpenRouter API key
4. Start the FastAPI server

Alternatively, you can start the server manually:

```bash
uvicorn app:app --reload
```

The API will be available at http://localhost:8000

## OpenRouter Integration

This backend uses [OpenRouter](https://openrouter.ai/) as the AI provider, which offers:

- Access to multiple AI models through a single API
- Free tier with Mistral 7B Instruct model
- Pay-as-you-go pricing for premium models
- No need for OpenAI API keys

### API Key Management

The backend includes several utilities for OpenRouter API key management:

- `setup_env.py`: Interactive script to configure your API key
- `test_openrouter.py`: Validate your API key and view available models
- API endpoints for key validation and model listing

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## API Endpoints

### Core PCB Analysis Endpoints
- `POST /upload_pcb`: Upload a PCB JSON file and initialize a session
- `GET /board/{board_id}/nets`: Get all nets in a PCB with component and pad counts
- `POST /board/{board_id}/calculate_trace`: Calculate trace length between two pads
- `POST /board/{board_id}/analyze`: AI-powered PCB analysis

### OpenRouter API Key Management
- `GET /api/keys/validate`: Check if the configured API key is valid
- `POST /api/keys/validate`: Validate a provided API key
- `GET /api/keys/models`: Get available models with the configured API key

## Development

- The backend integrates with the `trace_extractor.py` module for PCB analysis
- In-memory session storage is used for development (can be replaced with a database)
- The project structure is organized for easy extension with additional endpoints
- AI analysis is powered by OpenRouter through LangChain integration 