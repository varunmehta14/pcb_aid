import json
import os
import time
import threading
import concurrent.futures
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
    
    def __init__(self, pcb_data: Dict[str, Any], api_key: Optional[str] = None, model_name: Optional[str] = None, timeout: int = 30):
        """Initialize with PCB data and optional API key.
        
        Args:
            pcb_data: Dictionary containing PCB data
            api_key: OpenRouter API key
            model_name: Optional model name, defaults to gpt-3.5-turbo if None
            timeout: Maximum time in seconds for operations to complete (default: 30s)
        """
        self.pcb_data = pcb_data
        self.api_key = api_key
        self.timeout = timeout
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
                    temperature=ANALYSIS_TEMPERATURE,
                    request_timeout=self.timeout  # Add timeout for LLM requests
                )
                print(f"Initialized LLM with model: {self.model_name}")
            except Exception as e:
                print(f"Error initializing LLM with model {self.model_name}: {str(e)}")
                self.llm = None
        else:
            self.llm = None
    
    def run_with_timeout(self, func, *args, **kwargs):
        """Run a function with a timeout to prevent hanging.
        
        Args:
            func: Function to run
            *args: Arguments to pass to function
            **kwargs: Keyword arguments to pass to function
            
        Returns:
            Function result or error message
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=self.timeout)
            except concurrent.futures.TimeoutError:
                print(f"Operation timed out after {self.timeout} seconds")
                return f"Analysis timed out after {self.timeout} seconds. Please try a more specific query."
            except Exception as e:
                print(f"Error during execution: {str(e)}")
                return f"Error during analysis: {str(e)}"
    
    def analyze_pcb_safely(self, query_type: str) -> str:
        """Safely run a specific analysis type with error handling and timeout.
        
        Args:
            query_type: Type of analysis to run ("analyze trace lengths", etc.)
            
        Returns:
            Analysis result or error message
        """
        print(f"Running '{query_type}' analysis...")
        
        # Use timeout mechanism
        return self.run_with_timeout(self._analyze_pcb_implementation, query_type)
    
    def _analyze_pcb_implementation(self, query_type: str) -> str:
        """Internal implementation of PCB analysis (called with timeout).
        
        Args:
            query_type: Type of analysis to run
            
        Returns:
            Analysis result
        """
        try:
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
        start_time = time.time()
        
        # Extract specific components and pads from the query if present
        components_pads = self.extract_components_pads(query)
        if components_pads:
            print(f"Detected specific component(s) and pad(s) in query: {components_pads}")
            # Modify query to analyze specific trace
            return self.analyze_specific_trace(components_pads, query)
        
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
            
            # Check if we've reached timeout
            if time.time() - start_time > self.timeout:
                return f"Analysis timed out after {self.timeout} seconds. Please try a more specific query."
            
            # If LLM is available, enhance the response
            if self.llm:
                try:
                    print(f"Using LLM model {self.model_name} to enhance response...")
                    prompt = f"""Based on the following PCB analysis, provide a detailed response to the query: "{query}"
                    
{result}

Provide specific insights and recommendations based on this PCB data.
                    """
                    
                    # Use timeout for LLM call
                    llm_response = self.run_with_timeout(self.llm.invoke, prompt)
                    if isinstance(llm_response, str):
                        # It's an error message
                        return result
                    return llm_response.content
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
    
    def extract_components_pads(self, query: str) -> List[Dict]:
        """Extract specific component and pad information from a query.
        
        Args:
            query: Natural language query about PCB
            
        Returns:
            List of dictionaries with component and pad info, or empty list if none found
        """
        components_pads = []
        
        # Look for patterns like designator "U1", padnumber "11"
        import re
        designator_pattern = r'designator\s*["\']([^"\']+)["\']'
        pad_pattern = r'padnumber\s*["\']([^"\']+)["\']'
        
        designators = re.findall(designator_pattern, query, re.IGNORECASE)
        pads = re.findall(pad_pattern, query, re.IGNORECASE)
        
        # If we have both designators and pads, pair them
        if len(designators) == len(pads) and len(designators) >= 2:
            for i in range(len(designators)):
                components_pads.append({
                    "designator": designators[i],
                    "pad": pads[i]
                })
        
        return components_pads
    
    def analyze_specific_trace(self, components_pads: List[Dict], original_query: str) -> str:
        """Analyze a specific trace between components and pads.
        
        Args:
            components_pads: List of component/pad pairs
            original_query: Original query for context
            
        Returns:
            Analysis result for the specific trace
        """
        if len(components_pads) < 2:
            return "Unable to analyze a specific trace without at least two components and pads."
        
        start = components_pads[0]
        end = components_pads[1]
        
        try:
            # Use PCBTraceExtractor to get trace information
            from trace_extractor import PCBTraceExtractor
            extractor = PCBTraceExtractor(self.pcb_data)
            
            # Analyze the specific trace
            path_info = self.run_with_timeout(
                extractor.get_trace_path,
                start["designator"],
                start["pad"],
                end["designator"],
                end["pad"]
            )
            
            if isinstance(path_info, str):
                # It's an error message
                return path_info
            
            if not path_info.get('path_exists', False):
                return f"No direct trace found between {start['designator']} pad {start['pad']} and {end['designator']} pad {end['pad']}."
            
            # Format the result
            result = f"""
Trace Analysis from {start['designator']} pad {start['pad']} to {end['designator']} pad {end['pad']}:

Length: {path_info.get('length_mm', 'N/A')} mm
Path: {path_info.get('path_description', 'N/A')}
            """
            
            # Enhance with LLM if available
            if self.llm:
                try:
                    print(f"Using LLM model {self.model_name} to enhance specific trace analysis...")
                    prompt = f"""
I'm analyzing a PCB trace between {start['designator']} pad {start['pad']} and {end['designator']} pad {end['pad']}.

The trace has a length of {path_info.get('length_mm', 'N/A')} mm.
The path description is: {path_info.get('path_description', 'N/A')}

Based on this information, please provide a detailed analysis of this trace. Consider factors like signal integrity, 
potential issues with the trace length, and any recommendations for optimization.

Original user query: "{original_query}"
                    """
                    
                    # Use timeout for LLM call
                    llm_response = self.run_with_timeout(self.llm.invoke, prompt)
                    if isinstance(llm_response, str):
                        # It's an error message
                        return result
                    return llm_response.content
                except Exception as llm_error:
                    print(f"Error using LLM to enhance specific trace analysis: {str(llm_error)}")
                    print("Falling back to raw analysis")
                    return result
            
            return result
            
        except Exception as e:
            error_msg = f"Error analyzing specific trace: {str(e)}"
            print(error_msg)
            return error_msg
    
    @classmethod
    def get_reliable_models(cls) -> List[str]:
        """Get the list of reliable models that work with this analyzer.
        
        Returns:
            List of model names that are known to work reliably
        """
        return cls.RELIABLE_MODELS 