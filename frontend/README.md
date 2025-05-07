# PCB AiD - Frontend

This is the React frontend for the PCB AiD (Analyzer & Intelligent Design Assistant) application.

## Features

- PCB file upload
- Interactive net visualization
- Trace length inspection between pads
- Critical path analysis
- Integration with FastAPI backend

## Tech Stack

- React
- TypeScript
- Vite
- Chakra UI (for styling)
- Zustand (state management)
- Axios (API requests)

## Setup & Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at http://localhost:5173 and will proxy API requests to the FastAPI backend running on http://localhost:8000.

## Build for Production

```bash
npm run build
```

This will create a production build in the `dist` directory.

## Project Structure

- `src/`: Main source code
  - `api/`: API service functions
  - `components/`: Reusable React components
  - `pages/`: Page components
  - `store/`: Zustand store (state management)
  - `types/`: TypeScript type definitions
  - `App.tsx`: Main app component
  - `main.tsx`: Entry point

## Development

- The frontend connects to the FastAPI backend through API calls
- File upload is implemented using a drag-and-drop component
- Net visualization uses the provided PCB data
- All UI components are built with Chakra UI for consistent styling 