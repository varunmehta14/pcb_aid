"""Configuration for the AI module."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# LLM model configurations
# DEFAULT_MODEL = "mistralai/mistral-7b-instruct:free"  # Free tier model on OpenRouter
DEFAULT_MODEL = "openai/gpt-3.5-turbo"
FALLBACK_MODEL = "openai/gpt-3.5-turbo"  # Premium model (only used if needed)

# Temperature settings
ANALYSIS_TEMPERATURE = 0.0
OPTIMIZATION_TEMPERATURE = 0.7

# Tool configurations
TRACE_LENGTH_THRESHOLD = 100  # mm
COMPONENT_COUNT_THRESHOLD = 10 