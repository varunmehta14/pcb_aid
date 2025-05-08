from typing import List
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from ..tools.pcb_tools import PCBAnalysisTool
from ..config import (
    DEFAULT_MODEL,
    ANALYSIS_TEMPERATURE,
    OPTIMIZATION_TEMPERATURE,
    OPENROUTER_BASE_URL,
    FALLBACK_MODEL
)

class PCBAnalysisAgent:
    def __init__(self, pcb_data: dict, openrouter_api_key: str):
        self.pcb_data = pcb_data
        self.api_key = openrouter_api_key
        
        try:
            # Initialize the LLM with OpenRouter
            if self.api_key:
                self.llm = ChatOpenAI(
                    model=DEFAULT_MODEL,
                    base_url=OPENROUTER_BASE_URL,
                    api_key=self.api_key,
                    temperature=ANALYSIS_TEMPERATURE
                )
            else:
                self.llm = None
        except Exception as e:
            print(f"Error initializing OpenRouter ChatOpenAI: {e}")
            self.llm = None
            
        self.tools = self._create_tools()
        
        # Only create the agent if we have a valid LLM
        if self.llm:
            try:
                self.agent = self._create_agent()
            except Exception as e:
                print(f"Error creating agent: {e}")
                self.agent = None
        else:
            self.agent = None
    
    def _create_tools(self) -> List[Tool]:
        """Create the tools available to the agent."""
        tool = PCBAnalysisTool(pcb_data=self.pcb_data)
        return [tool]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the agent with its tools and prompt."""
        prompt = PromptTemplate.from_template(
            """You are an expert PCB design analyst. Your goal is to help analyze and optimize PCB layouts.
            
            Use the following tools to analyze the PCB:
            {tools}
            
            To use a tool, follow this format strictly:
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            
            After using a tool, think about the result and decide if you need to use another tool or if you can provide a final answer.
            
            IMPORTANT: Never provide both an Action and a Final Answer in the same response. Either use an Action or give a Final Answer, not both.
            
            When you have a final answer, respond with:
            Final Answer: your detailed analysis and recommendations
            
            Question: {input}
            {agent_scratchpad}"""
        )
        
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True  # Add this to handle parsing errors gracefully
        )
    
    def analyze(self, query: str) -> str:
        """Run the agent with a natural language query about the PCB."""
        # If the agent wasn't created (likely due to API key issues), go straight to direct tool usage
        if not self.agent:
            print("Agent not available. Using direct tool calls.")
            try:
                # Direct tool usage without agent framework
                tool = self.tools[0]
                if "trace length" in query.lower():
                    return tool._run("analyze trace lengths")
                elif "critical path" in query.lower():
                    return tool._run("analyze critical paths")
                elif "design issue" in query.lower() or "issues" in query.lower():
                    return tool._run("analyze design issues")
                else:
                    # Run a combination of analyses
                    return f"""
Analysis Results:

Trace Length Analysis:
{tool._run("analyze trace lengths")}

Critical Path Analysis:
{tool._run("analyze critical paths")}

Design Issues:
{tool._run("analyze design issues")}
                    """
            except Exception as e:
                return f"Error analyzing PCB with direct tool calls: {str(e)}"
                
        # If we have an agent, try the normal path
        try:
            # First try the agent-based approach
            return self.agent.invoke({"input": query})["output"]
        except Exception as e:
            print(f"Agent execution failed: {str(e)}. Falling back to direct tool usage.")
            try:
                # Fallback 1: Direct tool usage without agent framework
                if "trace length" in query.lower():
                    tool = self.tools[0]
                    return tool._run("analyze trace lengths")
                elif "critical path" in query.lower():
                    tool = self.tools[0]
                    return tool._run("analyze critical paths")
                elif "design issue" in query.lower() or "issues" in query.lower():
                    tool = self.tools[0]
                    return tool._run("analyze design issues")
                else:
                    # Fallback 2: Use a simple LLM call if available
                    if self.llm:
                        fallback_llm = ChatOpenAI(
                            model=FALLBACK_MODEL,
                            base_url=OPENROUTER_BASE_URL,
                            api_key=self.api_key,
                            temperature=ANALYSIS_TEMPERATURE
                        )
                        return fallback_llm.invoke(f"Analyze this PCB design: {query}")
                    else:
                        # No LLM available, run all analysis tools
                        tool = self.tools[0]
                        return f"""
Analysis Results:

Trace Length Analysis:
{tool._run("analyze trace lengths")}

Critical Path Analysis:
{tool._run("analyze critical paths")}

Design Issues:
{tool._run("analyze design issues")}
                        """
            except Exception as second_e:
                # If everything fails, return a simple message
                return f"Could not analyze PCB due to errors: {str(e)} and {str(second_e)}. Please check the PCB data format."

class PCBDesignOptimizer:
    def __init__(self, pcb_data: dict, openrouter_api_key: str):
        self.pcb_data = pcb_data
        self.api_key = openrouter_api_key
        
        try:
            # Initialize the LLM with OpenRouter
            if self.api_key:
                self.llm = ChatOpenAI(
                    model=DEFAULT_MODEL,
                    base_url=OPENROUTER_BASE_URL,
                    api_key=self.api_key,
                    temperature=OPTIMIZATION_TEMPERATURE
                )
            else:
                self.llm = None
        except Exception as e:
            print(f"Error initializing OpenRouter ChatOpenAI: {e}")
            self.llm = None
            
        self.tools = self._create_tools()
        
        # Only create the agent if we have a valid LLM
        if self.llm:
            try:
                self.agent = self._create_agent()
            except Exception as e:
                print(f"Error creating optimizer agent: {e}")
                self.agent = None
        else:
            self.agent = None
    
    def _create_tools(self) -> List[Tool]:
        """Create the tools available to the optimizer."""
        tool = PCBAnalysisTool(pcb_data=self.pcb_data)
        return [tool]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the optimizer agent with its tools and prompt."""
        prompt = PromptTemplate.from_template(
            """You are an expert PCB design optimizer. Your goal is to suggest improvements to the PCB layout.
            
            Use the following tools to analyze the PCB:
            {tools}
            
            To use a tool, follow this format strictly:
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            
            After using a tool, think about the result and decide if you need to use another tool or if you can provide a final answer.
            
            IMPORTANT: Never provide both an Action and a Final Answer in the same response. Either use an Action or give a Final Answer, not both.
            
            When you have a final answer, respond with:
            Final Answer: your detailed optimization suggestions and improvements
            
            Question: {input}
            {agent_scratchpad}"""
        )
        
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True  # Add this to handle parsing errors gracefully
        )
    
    def optimize(self, query: str) -> str:
        """Run the optimizer with a natural language query about PCB improvements."""
        # If the agent wasn't created (likely due to API key issues), go straight to direct tool usage
        if not self.agent:
            print("Optimizer agent not available. Using direct tool calls.")
            try:
                # Direct tool usage without agent framework
                tool = self.tools[0]
                
                # Get basic analysis
                analysis = ""
                try:
                    analysis = f"""
Trace Length Analysis:
{tool._run("analyze trace lengths")}

Critical Path Analysis:
{tool._run("analyze critical paths")}

Design Issues:
{tool._run("analyze design issues")}
                    """
                except Exception as analysis_e:
                    analysis = f"Error getting analysis: {str(analysis_e)}"
                
                return f"""
Based on the PCB data, here are optimization suggestions:

{analysis}

Consider:
- Shorter trace lengths for high-frequency signals
- Better component placement to minimize trace crossing
- Optimized ground plane connections
                """
            except Exception as e:
                return f"Error optimizing PCB with direct tool calls: {str(e)}"
                
        # If we have an agent, try the normal path
        try:
            # First try the agent-based approach
            return self.agent.invoke({"input": query})["output"]
        except Exception as e:
            print(f"Optimizer execution failed: {str(e)}. Falling back to direct tool usage.")
            try:
                # Fallback 1: Direct tool usage without agent framework
                tool = self.tools[0]
                
                # Get basic analysis to inform the optimization
                analysis = ""
                try:
                    if "trace length" in query.lower():
                        analysis = tool._run("analyze trace lengths")
                    elif "critical path" in query.lower():
                        analysis = tool._run("analyze critical paths")
                    else:
                        analysis = tool._run("analyze design issues")
                except:
                    analysis = "No detailed analysis available."
                
                # Fallback 2: Use a simple LLM call with the analysis if available
                if self.llm:
                    fallback_llm = ChatOpenAI(
                        model=FALLBACK_MODEL,
                        base_url=OPENROUTER_BASE_URL,
                        api_key=self.api_key,
                        temperature=ANALYSIS_TEMPERATURE
                    )
                    
                    prompt = f"""
                    Based on the following PCB analysis, suggest improvements and optimizations:
                    
                    {analysis}
                    
                    The original query was: {query}
                    
                    Provide specific, actionable suggestions for improving the PCB design.
                    """
                    
                    return fallback_llm.invoke(prompt)
                else:
                    # No LLM available, provide simple suggestions based on analysis
                    return f"""
Based on the PCB analysis:

{analysis}

Optimization Suggestions:
- Consider shorter trace lengths for high-frequency signals
- Optimize component placement to minimize trace crossings
- Ensure good ground plane connectivity
- Minimize vias in critical signal paths
                    """
                
            except Exception as second_e:
                # If everything fails, return a simple message
                return f"Could not optimize PCB due to errors: {str(e)} and {str(second_e)}. Please check the PCB data format." 