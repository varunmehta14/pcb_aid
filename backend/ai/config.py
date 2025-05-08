"""
Configuration settings for the AI workflow and tools.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model settings
DEFAULT_MODEL = "mistralai/mistral-7b-instruct:free"  # Free tier model on OpenRouter
FALLBACK_MODEL = "openai/gpt-3.5-turbo"  # Premium model (only used if needed)
ANALYSIS_TEMPERATURE = 0.2
OPTIMIZATION_TEMPERATURE = 0.5

# PCB Analysis thresholds
TRACE_LENGTH_THRESHOLD = 50.0  # mm - traces longer than this are considered critical
COMPONENT_COUNT_THRESHOLD = 10  # components per net - nets with more components might be problematic

# Graph settings for trace extraction
CONNECTION_TOLERANCE = 2.0  # mils - how close objects need to be to be considered connected 