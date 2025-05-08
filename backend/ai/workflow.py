from typing import Dict, List, Any
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from .agents.pcb_agents import PCBAnalysisAgent, PCBDesignOptimizer
from .config import DEFAULT_MODEL, ANALYSIS_TEMPERATURE, OPENROUTER_BASE_URL

class PCBWorkflow:
    def __init__(self, pcb_data: dict, openrouter_api_key: str):
        # Validate PCB data
        if pcb_data is None:
            raise ValueError("PCB data cannot be None")
            
        # Additional validation to ensure it's a dictionary with expected keys
        if not isinstance(pcb_data, dict):
            raise ValueError(f"PCB data must be a dictionary, got {type(pcb_data)}")
            
        # Check for required keys in pcb_data
        required_keys = ["components", "tracks"]
        for key in required_keys:
            if key not in pcb_data:
                raise ValueError(f"PCB data is missing required key: {key}")
                
        self.pcb_data = pcb_data
        self.api_key = openrouter_api_key
        self.analysis_agent = PCBAnalysisAgent(pcb_data, openrouter_api_key)
        self.optimizer = PCBDesignOptimizer(pcb_data, openrouter_api_key)
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> Graph:
        """Create the LangGraph workflow for PCB analysis."""
        
        # Define the state schema
        def get_initial_state():
            return {
                "messages": [],  # Empty list by default, will be populated in process_query
                "analysis": "",
                "optimization": "",
                "error": None
            }
        
        # Define the nodes
        def analyze_pcb(state: Dict[str, Any]) -> Dict[str, Any]:
            """Analyze the PCB using the analysis agent."""
            try:
                # Ensure there's at least one message
                if not state["messages"]:
                    # Default query if no messages exist
                    query = "Analyze this PCB design"
                else:
                    query = state["messages"][-1]["content"]
                    
                state["analysis"] = self.analysis_agent.analyze(query)
                return state
            except Exception as e:
                state["error"] = f"Error during PCB analysis: {str(e)}"
                return state
        
        def optimize_pcb(state: Dict[str, Any]) -> Dict[str, Any]:
            """Optimize the PCB using the optimizer agent."""
            try:
                # If there was an error in analysis, skip optimization
                if state.get("error"):
                    return state
                    
                # Ensure there's at least one message
                if not state["messages"]:
                    # Default query if no messages exist
                    query = "Suggest improvements for this PCB design"
                else:
                    query = state["messages"][-1]["content"]
                    
                state["optimization"] = self.optimizer.optimize(query)
                return state
            except Exception as e:
                state["error"] = f"Error during PCB optimization: {str(e)}"
                return state
        
        def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
            """Generate a final response combining analysis and optimization."""
            try:
                # If there was an error, return a helpful error message
                if state.get("error"):
                    state["messages"].append({
                        "role": "assistant", 
                        "content": f"I encountered an error while analyzing your PCB: {state['error']}. Please check that your PCB data is valid and try again."
                    })
                    return state
                    
                llm = ChatOpenAI(
                    model=DEFAULT_MODEL,
                    temperature=ANALYSIS_TEMPERATURE,
                    base_url=OPENROUTER_BASE_URL,
                    api_key=self.api_key
                )
                
                prompt = f"""Based on the following analysis and optimization suggestions, provide a comprehensive response:
                
                Analysis:
                {state["analysis"]}
                
                Optimization Suggestions:
                {state["optimization"]}
                
                Please provide a clear, well-structured response that combines both the analysis and optimization suggestions."""
                
                response = llm.invoke([HumanMessage(content=prompt)])
                state["messages"].append({"role": "assistant", "content": response.content})
                return state
            except Exception as e:
                # If an error occurs in response generation, provide a basic response with the raw data
                state["messages"].append({
                    "role": "assistant", 
                    "content": f"""I encountered an error while formatting the response, but here's the raw analysis:
                    
                    Analysis:
                    {state["analysis"]}
                    
                    Optimization Suggestions:
                    {state["optimization"]}
                    
                    Error: {str(e)}"""
                })
                return state
        
        # Create the graph
        workflow = StateGraph(get_initial_state)
        
        # Add nodes
        workflow.add_node("analyze", analyze_pcb)
        workflow.add_node("optimize", optimize_pcb)
        workflow.add_node("generate_response", generate_response)
        
        # Add edges
        workflow.add_edge("analyze", "optimize")
        workflow.add_edge("optimize", "generate_response")
        
        # Set entry and exit points
        workflow.set_entry_point("analyze")
        workflow.set_finish_point("generate_response")
        
        return workflow.compile()
    
    def process_query(self, query: str) -> str:
        """Process a natural language query about the PCB."""
        try:
            # Initialize state as a dictionary
            state = {
                "messages": [{"role": "user", "content": query}],
                "analysis": "",
                "optimization": "",
                "error": None
            }
            
            # Print debug info
            print(f"PCB data type: {type(self.pcb_data)}")
            if isinstance(self.pcb_data, dict):
                print(f"PCB data keys: {self.pcb_data.keys()}")
                print(f"Components length: {len(self.pcb_data.get('components', []))}")
            
            # Run the workflow
            print("Running workflow...")
            final_state = self.workflow.invoke(state)
            print("Workflow completed")
            
            # Check if final_state is None (possible error from langgraph)
            if final_state is None:
                return "The workflow could not be completed. There might be an issue with the LangGraph execution."
            
            # Return the final response
            if "messages" in final_state and final_state["messages"] and len(final_state["messages"]) > 0:
                return final_state["messages"][-1]["content"]
            elif "error" in final_state and final_state["error"]:
                return f"Error during analysis: {final_state['error']}"
            else:
                return "The analysis completed but did not produce a response. This might indicate an issue with the AI agents."
                
        except Exception as e:
            # Print exception for debugging
            import traceback
            print(f"Error in process_query: {str(e)}")
            print(traceback.format_exc())
            
            # Check if it's an API key error and fall back to direct tool usage
            if "api_key" in str(e).lower() or "unauthorized" in str(e).lower() or "authentication" in str(e).lower() or "401" in str(e):
                try:
                    print("API authentication issue detected. Falling back to direct tool usage.")
                    tool = self.analysis_agent.tools[0]
                    
                    if "trace length" in query.lower():
                        return tool._run("analyze trace lengths")
                    elif "critical path" in query.lower():
                        return tool._run("analyze critical paths")
                    elif "design issue" in query.lower() or "issues" in query.lower():
                        return tool._run("analyze design issues")
                    else:
                        # Run all analysis types
                        trace_analysis = tool._run("analyze trace lengths")
                        critical_analysis = tool._run("analyze critical paths")
                        issue_analysis = tool._run("analyze design issues")
                        
                        return f"""PCB Analysis Results:
                        
Trace Length Analysis:
{trace_analysis}

Critical Path Analysis:
{critical_analysis}

Design Issues:
{issue_analysis}"""
                        
                except Exception as fallback_e:
                    return f"Error analyzing PCB: {str(e)}. Fallback analysis also failed: {str(fallback_e)}"
            else:
                return f"Error analyzing PCB: {str(e)}" 