import os
import asyncio
import functools
import operator
import uuid
import logging
from typing import Annotated, Sequence, TypedDict

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from tools import *
from setup_environment import set_environment_variables
from tools.pdf import OUTPUT_DIRECTORY
from tools.web import research
from tools.internet import scrape_webpages
from web_research_prompts import RESEARCHER_SYSTEM_PROMPT, TAVILY_AGENT_SYSTEM_PROMPT, RAG_SYSTEM_PROMPT

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

class WebResearchGraph:
    def __init__(self, llm=None):
        set_environment_variables("Web_Search_Graph")
        self.TAVILY_TOOL = TavilySearchResults(max_results=6)
        self.LLM = llm if llm else ChatOpenAI(model="gpt-4o-mini-2024-07-18")
        
        self.RAG_AGENT_NAME = "rag"
        self.TAVILY_AGENT_NAME = "researcher"
        self.RESEARCH_AGENT_NAME = "web scraper"
        self.SAVE_FILE_NODE_NAME = "writer"

    def create_agent(self, llm: ChatOpenAI, tools: list, system_prompt: str):
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        agent = create_openai_tools_agent(llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools)
        return executor

    def agent_node(self, state: AgentState, agent, name):
        result = agent.invoke(state)
        return {"messages": [HumanMessage(content=result["output"], name=name)]}

    async def async_agent_node(self, state: AgentState, agent, name):
        result = await agent.ainvoke(state)
        return {"messages": [HumanMessage(content=result["output"], name=name)]}

    def save_file_node(self, state: AgentState):
        markdown_content = str(state["messages"][-1].content)
        filename = f"{uuid.uuid4()}.md"
        full_path = os.path.join(OUTPUT_DIRECTORY, filename)
        with open(full_path, "w", encoding="utf-8") as file:
            file.write(markdown_content)
        return {
            "messages": [
                HumanMessage(
                    content=f"Output written successfully. <a href='output/{filename}' download>Click here to download the file</a>",
                    name=self.SAVE_FILE_NODE_NAME,
                )
            ]
        }

    def create_web_research_rag_graph(self):
        rag_agent = self.create_agent(self.LLM, [rag_query], RAG_SYSTEM_PROMPT)
        rag_agent_node = functools.partial(self.agent_node, agent=rag_agent, name=self.RAG_AGENT_NAME)

        tavily_agent = self.create_agent(self.LLM, [self.TAVILY_TOOL], TAVILY_AGENT_SYSTEM_PROMPT)
        tavily_agent_node = functools.partial(self.agent_node, agent=tavily_agent, name=self.TAVILY_AGENT_NAME)

        research_agent = self.create_agent(self.LLM, [research], RESEARCHER_SYSTEM_PROMPT)
        research_agent_node = functools.partial(self.async_agent_node, agent=research_agent, name=self.RESEARCH_AGENT_NAME)

        workflow = StateGraph(AgentState)
        workflow.add_node(self.RAG_AGENT_NAME, rag_agent_node)
        workflow.add_node(self.TAVILY_AGENT_NAME, tavily_agent_node)
        workflow.add_node(self.RESEARCH_AGENT_NAME, research_agent_node)
        workflow.add_node(self.SAVE_FILE_NODE_NAME, self.save_file_node)

        workflow.add_edge(self.RAG_AGENT_NAME, self.TAVILY_AGENT_NAME)
        workflow.add_edge(self.TAVILY_AGENT_NAME, self.RESEARCH_AGENT_NAME)
        workflow.add_edge(self.RESEARCH_AGENT_NAME, self.SAVE_FILE_NODE_NAME)
        workflow.add_edge(self.SAVE_FILE_NODE_NAME, END)

        workflow.set_entry_point(self.RAG_AGENT_NAME)
        return workflow.compile()

    def create_web_research_graph(self):
        tavily_agent = self.create_agent(self.LLM, [self.TAVILY_TOOL], TAVILY_AGENT_SYSTEM_PROMPT)
        tavily_agent_node = functools.partial(self.agent_node, agent=tavily_agent, name=self.TAVILY_AGENT_NAME)

        research_agent = self.create_agent(self.LLM, [research, scrape_webpages], RESEARCHER_SYSTEM_PROMPT)
        research_agent_node = functools.partial(self.async_agent_node, agent=research_agent, name=self.RESEARCH_AGENT_NAME)

        workflow = StateGraph(AgentState)
        workflow.add_node(self.TAVILY_AGENT_NAME, tavily_agent_node)
        workflow.add_node(self.RESEARCH_AGENT_NAME, research_agent_node)
        workflow.add_node(self.SAVE_FILE_NODE_NAME, self.save_file_node)

        workflow.add_edge(self.TAVILY_AGENT_NAME, self.RESEARCH_AGENT_NAME)
        workflow.add_edge(self.RESEARCH_AGENT_NAME, self.SAVE_FILE_NODE_NAME)
        workflow.add_edge(self.SAVE_FILE_NODE_NAME, END)

        workflow.set_entry_point(self.TAVILY_AGENT_NAME)
        return workflow.compile()

# Usage
web_research = WebResearchGraph()
rag_graph = web_research.create_web_research_rag_graph()
research_graph = web_research.create_web_research_graph()

# Run the graphs
async def run_research_graph(graph, input):
    async for output in graph.astream(input):
        for node_name, output_value in output.items():
            print("---")
            print(f"Output from node '{node_name}':")
            print(output_value)
        print("\n---\n")

if __name__ == "__main__":
    #Enable logging
    logging.basicConfig(level=logging.INFO)

    test_input_norag = {"messages": [HumanMessage(content="Despicable Me")]}
    asyncio.run(run_research_graph(research_graph, test_input_norag))

    query = "Help me plan a 2-days trip including Bradford, Carlisles and the castles on the way from Bradford to Carlisles?"
    file_path = "D:\code\langgraph_agents\output\Bradford-1day.pdf, D:\code\langgraph_agents\output\Bradford-Carlisle-2days-Itinerary.md"
    
    test_input_rag = {
        "messages": [
            HumanMessage(content=f"Query: {query}\nFile Path: {file_path}")
        ]
    }
    logging.info("Starting research graph with test input")
    asyncio.run(run_research_graph(rag_graph, test_input_rag))
    logging.info("Research graph completed")
