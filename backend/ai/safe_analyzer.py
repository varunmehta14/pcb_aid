import json
import os
from typing import Dict, Optional, List, Any
from .tools.pcb_tools import PCBAnalysisTool
from langchain_openai import ChatOpenAI
from .config import ANALYSIS_TEMPERATURE, OPENROUTER_BASE_URL

class SafePCBAnalyzer:
    """A safe PCB analyzer class that uses direct tool access instead of agents.
    
    This analyzer avoids the agent framework issues by directly calling the PCBAnalysisTool
    and using a reliable LLM model to enhance the responses when needed.
    """
    
    # List of models known to work with PCB analysis based on testing
    RELIABLE_MODELS = [
        "openai/gpt-3.5-turbo",  # Reliable and widely available
        "mistralai/mistral-small",  # Good alternative
    ]
    
    def __init__(self, pcb_data: Dict[str, Any], api_key: Optional[str] = None, model_name: Optional[str] = None):
        """Initialize with PCB data and optional API key.
        
        Args:
            pcb_data: Dictionary containing PCB data
            api_key: OpenRouter API key
            model_name: Optional model name, defaults to gpt-3.5-turbo if None
        """
        self.pcb_data = pcb_data
        self.api_key = api_key
        self.tool = PCBAnalysisTool(pcb_data=pcb_data)
        
        # Use the specified model or default to first reliable model
        if model_name is None:
            self.model_name = self.RELIABLE_MODELS[0]
        else:
            self.model_name = model_name
            
        # Initialize LLM if API key is available
        if api_key:
            try:
                self.llm = ChatOpenAI(
                    model=self.model_name,
                    base_url=OPENROUTER_BASE_URL,
                    api_key=api_key,
                    temperature=ANALYSIS_TEMPERATURE
                )
                print(f"Initialized LLM with model: {self.model_name}")
            except Exception as e:
                print(f"Error initializing LLM with model {self.model_name}: {str(e)}")
                self.llm = None
        else:
            self.llm = None
    
    def analyze_pcb_safely(self, query_type: str) -> str:
        """Safely run a specific analysis type with error handling.
        
        Args:
            query_type: Type of analysis to run ("analyze trace lengths", etc.)
            
        Returns:
            Analysis result or error message
        """
        try:
            print(f"Running '{query_type}' analysis...")
            result = self.tool._run(query_type)
            return result
        except Exception as e:
            error_msg = f"Error during '{query_type}' analysis: {str(e)}"
            print(error_msg)
            return error_msg
    
    def get_comprehensive_analysis(self) -> str:
        """Get a comprehensive analysis with error handling for each part.
        
        Returns:
            Combined analysis results
        """
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
        """Process a natural language query about the PCB.
        
        Args:
            query: Natural language query about PCB
            
        Returns:
            Analysis response
        """
        print(f"Processing query: '{query}'")
        
        try:
            # Check query type based on keywords
            if "trace length" in query.lower() or "traces" in query.lower():
                result = self.analyze_pcb_safely("analyze trace lengths")
            elif "critical path" in query.lower():
                result = self.analyze_pcb_safely("analyze critical paths")
            elif "design issue" in query.lower() or "issues" in query.lower():
                result = self.analyze_pcb_safely("analyze design issues")
            elif "redesign" in query.lower() or "all" in query.lower() or "comprehensive" in query.lower():
                # For redesign queries, get comprehensive analysis
                result = self.get_comprehensive_analysis()
            else:
                # For all other queries, get comprehensive analysis
                result = self.get_comprehensive_analysis()
            
            # If LLM is available, enhance the response
            if self.llm:
                try:
                    print(f"Using LLM model {self.model_name} to enhance response...")
                    prompt = f"""Based on the following PCB analysis, provide a detailed response to the query: "{query}"
                    
{result}

Provide specific insights and recommendations based on this PCB data.
                    """
                    
                    response = self.llm.invoke(prompt)
                    return response.content
                except Exception as llm_error:
                    print(f"Error using LLM to enhance response: {str(llm_error)}")
                    print("Falling back to raw analysis")
                    return result
            else:
                # Return raw analysis if LLM is not available
                return result
            
        except Exception as e:
            error_msg = f"Error analyzing PCB: {str(e)}"
            print(error_msg)
            return error_msg
    
    @classmethod
    def get_reliable_models(cls) -> List[str]:
        """Get the list of reliable models that work with this analyzer.
        
        Returns:
            List of model names that are known to work reliably
        """
        return cls.RELIABLE_MODELS 