from typing import Dict, List, Any
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from .agents.pcb_agents import PCBAnalysisAgent, PCBDesignOptimizer

class PCBWorkflow:
    def __init__(self, pcb_data: dict, openai_api_key: str):
        self.pcb_data = pcb_data
        self.openai_api_key = openai_api_key
        self.analysis_agent = PCBAnalysisAgent(pcb_data, openai_api_key)
        self.optimizer = PCBDesignOptimizer(pcb_data, openai_api_key)
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> Graph:
        """Create the LangGraph workflow for PCB analysis."""
        
        # Define the state schema
        def get_initial_state():
            return {
                "messages": [],  # Empty list by default, will be populated in process_query
                "analysis": "",
                "optimization": ""
            }
        
        # Define the nodes
        def analyze_pcb(state: Dict[str, Any]) -> Dict[str, Any]:
            """Analyze the PCB using the analysis agent."""
            # Ensure there's at least one message
            if not state["messages"]:
                # Default query if no messages exist
                query = "Analyze this PCB design"
            else:
                query = state["messages"][-1]["content"]
                
            state["analysis"] = self.analysis_agent.analyze(query)
            return state
        
        def optimize_pcb(state: Dict[str, Any]) -> Dict[str, Any]:
            """Optimize the PCB using the optimizer agent."""
            # Ensure there's at least one message
            if not state["messages"]:
                # Default query if no messages exist
                query = "Suggest improvements for this PCB design"
            else:
                query = state["messages"][-1]["content"]
                
            state["optimization"] = self.optimizer.optimize(query)
            return state
        
        def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
            """Generate a final response combining analysis and optimization."""
            llm = ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=0,
                api_key=self.openai_api_key
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
        # Initialize state as a dictionary
        state = {
            "messages": [{"role": "user", "content": query}],
            "analysis": "",
            "optimization": ""
        }
        
        # Run the workflow
        final_state = self.workflow.invoke(state)
        
        # Return the final response
        return final_state["messages"][-1]["content"] 