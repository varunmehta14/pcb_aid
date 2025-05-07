# PCB AiD (Analyzer & Intelligent Design Assistant)

A sophisticated web application for analyzing Printed Circuit Board (PCB) layouts, combining interactive visualization, precise trace length calculation, critical path analysis, and AI-powered insights.

## Project Overview

PCB AiD is designed to help hardware engineers with design verification and optimization by:

1. Extracting detailed net topology for AI consumption
2. Providing interactive visualization of nets and trace paths
3. Identifying traces that violate user-defined design rules
4. Offering AI-powered insights through natural language queries

## Repository Structure

This repository is organized into two main components:

- `backend/`: FastAPI Python backend
- `frontend/`: React TypeScript frontend

Core functionality is provided by the `trace_extractor.py` module, which handles PCB data processing and trace length calculations.

## Setup & Running

### Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
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

4. Run the development server:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at http://localhost:8000

### Frontend (React)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at http://localhost:5173

## Features & Capabilities

- **PCB File Upload**: Upload and process PCB layout data in JSON format
- **Net Visualization**: Interactive 2D visualization of PCB nets
- **Trace Length Calculation**: Precise calculation of trace lengths between pads
- **Path Description**: Detailed description of paths between pads
- **Critical Path Analysis**: Identify traces that violate design rules
- **AI-Powered Insights**: Natural language queries about the PCB design (future)

## Key API Endpoints

- **`POST /upload_pcb`**: Upload PCB data
- **`GET /board/{board_id}/nets`**: Get list of nets
- **`POST /board/{board_id}/calculate_trace`**: Calculate trace length between pads
- **`POST /board/{board_id}/analyze_net_topology/{net_name}`**: Get detailed net topology
- **`POST /board/{board_id}/critical_path_analysis`**: Analyze critical paths

## Development Roadmap

1. **Phase 1 (Core Features)**:
   - Backend API endpoints for PCB data processing
   - Frontend for file upload and basic visualization
   - Trace length calculation functionality

2. **Phase 2 (Advanced Analysis)**:
   - Critical path analysis
   - Net topology exporter
   - Enhanced visualization

3. **Phase 3 (AI Integration)**:
   - LangGraph/CrewAI agent system
   - Natural language query interface
   - AI-powered design insights

## Contributing

Contributions to PCB AiD are welcome. Please feel free to submit a pull request.

## License

[MIT License](LICENSE)

## Contact

For questions or feedback, please open an issue in this repository. 