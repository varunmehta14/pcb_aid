import json
import os
from dotenv import load_dotenv
from ai.workflow import PCBWorkflow
from ai.tools.pcb_tools import PCBAnalysisTool
from fastapi import FastAPI, APIRouter, Request, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from ai.config import (
    DEFAULT_MODEL,
    ANALYSIS_TEMPERATURE,
    OPENROUTER_BASE_URL
)

# Load environment variables
load_dotenv()

class SafePCBAnalyzer:
    """A safe PCB analyzer class that uses direct tool access instead of agents."""
    
    def __init__(self, pcb_data: dict, api_key: str = None):
        """Initialize with PCB data and optional API key."""
        self.pcb_data = pcb_data
        self.api_key = api_key
        self.tool = PCBAnalysisTool(pcb_data=pcb_data)
        
        # Initialize LLM if API key is available
        if api_key:
            try:
                self.llm = ChatOpenAI(
                    model=DEFAULT_MODEL,
                    base_url=OPENROUTER_BASE_URL,
                    api_key=api_key,
                    temperature=ANALYSIS_TEMPERATURE
                )
            except Exception as e:
                print(f"Error initializing LLM: {str(e)}")
                self.llm = None
        else:
            self.llm = None
    
    def analyze_pcb_safely(self, query_type: str) -> str:
        """Safely run a specific analysis type with error handling."""
        try:
            print(f"Running '{query_type}' analysis...")
            result = self.tool._run(query_type)
            return result
        except Exception as e:
            error_msg = f"Error during '{query_type}' analysis: {str(e)}"
            print(error_msg)
            return error_msg
    
    def get_comprehensive_analysis(self) -> str:
        """Get a comprehensive analysis with error handling for each part."""
        trace_analysis = self.analyze_pcb_safely("analyze trace lengths")
        critical_analysis = self.analyze_pcb_safely("analyze critical paths")
        issue_analysis = self.analyze_pcb_safely("analyze design issues")
        
        return f"""
Trace Length Analysis:
{trace_analysis}

Critical Path Analysis:
{critical_analysis}

Design Issues:
{issue_analysis}
        """
    
    def process_query(self, query: str) -> str:
        """Process a natural language query about the PCB."""
        print(f"Processing query: '{query}'")
        
        try:
            # Check query type based on keywords
            if "trace length" in query.lower() or "traces" in query.lower():
                result = self.analyze_pcb_safely("analyze trace lengths")
            elif "critical path" in query.lower():
                result = self.analyze_pcb_safely("analyze critical paths")
            elif "design issue" in query.lower() or "issues" in query.lower():
                result = self.analyze_pcb_safely("analyze design issues")
            else:
                # For all other queries, get comprehensive analysis
                result = self.get_comprehensive_analysis()
            
            # If LLM is available, enhance the response
            if self.llm:
                try:
                    print("Using LLM to enhance response...")
                    prompt = f"""Based on the following PCB analysis, provide a detailed response to the query: "{query}"
                    
{result}

Provide specific insights and recommendations based on this PCB data.
                    """
                    
                    response = self.llm.invoke(prompt)
                    return response.content
                except Exception as llm_error:
                    print(f"Error using LLM to enhance response: {str(llm_error)}")
                    # Fall back to raw analysis if LLM fails
                    return result
            else:
                # Return raw analysis if LLM is not available
                return result
            
        except Exception as e:
            error_msg = f"Error analyzing PCB: {str(e)}"
            print(error_msg)
            return error_msg

# Create a FastAPI router for testing
class QueryModel(BaseModel):
    query: str

router = APIRouter()

@router.post("/analyze")
async def analyze_pcb(request: QueryModel):
    """API endpoint to analyze PCB data."""
    try:
        # Load the sample PCB data for testing
        with open('test_data/sample_pcb.json', 'r') as f:
            pcb_data = json.load(f)
        
        # Get API key from environment
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Create the analyzer
        analyzer = SafePCBAnalyzer(pcb_data, api_key)
        
        # Process the query
        result = analyzer.process_query(request.query)
        
        return JSONResponse(content={"result": result})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Test the SafePCBAnalyzer directly
def test_safe_analyzer():
    """Test the SafePCBAnalyzer with sample data."""
    # Load the sample PCB data
    with open('test_data/sample_pcb.json', 'r') as f:
        pcb_data = json.load(f)
    
    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    # Create the analyzer
    analyzer = SafePCBAnalyzer(pcb_data, api_key)
    
    # Test with a problematic query
    problematic_query = "What are all the possible ways to redesign this PCB? I need a highly detailed response."
    print(f"\n\n=== Testing with problematic query: '{problematic_query}' ===")
    response = analyzer.process_query(problematic_query)
    print("\nResponse:")
    print(response)
    
    # Test with a specific query
    specific_query = "What are the trace lengths in this PCB?"
    print(f"\n\n=== Testing with specific query: '{specific_query}' ===")
    response = analyzer.process_query(specific_query)
    print("\nResponse:")
    print(response)

if __name__ == "__main__":
    test_safe_analyzer() 