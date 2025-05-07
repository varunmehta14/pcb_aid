from typing import List
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from ..tools.pcb_tools import PCBAnalysisTool

class PCBAnalysisAgent:
    def __init__(self, pcb_data: dict, openai_api_key: str):
        self.pcb_data = pcb_data
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            api_key=openai_api_key
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
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
            
            To use a tool, use the following format:
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            
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
            verbose=True
        )
    
    def analyze(self, query: str) -> str:
        """Run the agent with a natural language query about the PCB."""
        return self.agent.invoke({"input": query})["output"]

class PCBDesignOptimizer:
    def __init__(self, pcb_data: dict, openai_api_key: str):
        self.pcb_data = pcb_data
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7,  # Slightly higher temperature for more creative suggestions
            api_key=openai_api_key
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
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
            
            To use a tool, use the following format:
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            
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
            verbose=True
        )
    
    def optimize(self, query: str) -> str:
        """Run the optimizer with a natural language query about PCB improvements."""
        return self.agent.invoke({"input": query})["output"] 