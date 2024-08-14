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
from web_research_prompts import RESEARCHER_SYSTEM_PROMPT, TAVILY_AGENT_SYSTEM_PROMPT, RAG_SYSTEM_PROMPT

set_environment_variables("Web_Search_Graph")

TAVILY_TOOL = TavilySearchResults(max_results=6)
LLM = ChatOpenAI(model="gpt-4o-mini-2024-07-18")

#Enable logging
logging.basicConfig(level=logging.INFO)

RAG_AGENT_NAME = "rag"
TAVILY_AGENT_NAME = "researcher"
RESEARCH_AGENT_NAME = "web scraper"
SAVE_FILE_NODE_NAME = "writer"

def create_agent(llm: ChatOpenAI, tools: list, system_prompt: str):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools)  # type: ignore
    return executor

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

def agent_node(state: AgentState, agent, name):
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}


async def async_agent_node(state: AgentState, agent, name):
    result = await agent.ainvoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}




# This shows that the graph is really nothing but a state machine. We can just write any arbitrary function and use it as a node as long as we meet the conditions we set for the graph. The function takes the AgentState object as input, does whatever it wants to do, and then adds an update to the AgentState object as promised. It doesn’t matter that there is no agent or LLM in this step.

# In this case, we extract the markdown content from the state object’s last message [-1] which is the research node’s output. We then generate a random filename using the uuid module and write the markdown content to a file with that name and the .md extension. Finally, we return a message to the state object that the output was written successfully.
def save_file_node(state: AgentState):
    markdown_content = str(state["messages"][-1].content)
    filename = f"{OUTPUT_DIRECTORY}/{uuid.uuid4()}.md"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(markdown_content)
    return {
        "messages": [
            HumanMessage(
                content=f"Output written successfully to {filename}",
                name=SAVE_FILE_NODE_NAME,
            )
        ]
    }

def create_web_research_rag_graph():
    rag_agent = create_agent(LLM, [rag_query], RAG_SYSTEM_PROMPT)
    rag_agent_node = functools.partial(agent_node, agent=rag_agent, name=RAG_AGENT_NAME)

    tavily_agent = create_agent(LLM, [TAVILY_TOOL], TAVILY_AGENT_SYSTEM_PROMPT)
    tavily_agent_node = functools.partial(
        agent_node, agent=tavily_agent, name=TAVILY_AGENT_NAME
    )

    research_agent = create_agent(LLM, [research], RESEARCHER_SYSTEM_PROMPT)
    research_agent_node = functools.partial(
        async_agent_node, agent=research_agent, name=RESEARCH_AGENT_NAME
    )

    workflow = StateGraph(AgentState)
    workflow.add_node(RAG_AGENT_NAME, rag_agent_node)
    workflow.add_node(TAVILY_AGENT_NAME, tavily_agent_node)
    workflow.add_node(RESEARCH_AGENT_NAME, research_agent_node)
    workflow.add_node(SAVE_FILE_NODE_NAME, save_file_node)

    workflow.add_edge(RAG_AGENT_NAME, TAVILY_AGENT_NAME)
    workflow.add_edge(TAVILY_AGENT_NAME, RESEARCH_AGENT_NAME)
    # workflow.add_edge(TAVILY_AGENT_NAME, SAVE_FILE_NODE_NAME) # for demo
    workflow.add_edge(RESEARCH_AGENT_NAME, SAVE_FILE_NODE_NAME)
    workflow.add_edge(SAVE_FILE_NODE_NAME, END)

    workflow.set_entry_point(RAG_AGENT_NAME)
    research_graph = workflow.compile()
    return research_graph

research_graph = create_web_research_rag_graph()

async def run_research_graph(input):
    async for output in research_graph.astream(input):
        for node_name, output_value in output.items():
            print("---")
            print(f"Output from node '{node_name}':")
            print(output_value)
        print("\n---\n")

if __name__ == "__main__":
    query = "Help me plan a 2-days trip including Bradford, Carlisles and the castles on the way from Bradford to Carlisles?"
    file_path = "D:\code\langgraph_agents\output\Bradford-1day.pdf, D:\code\langgraph_agents\output\Bradford-Carlisle-2days-Itinerary.md"
    
    test_input = {
        "messages": [
            HumanMessage(content=f"Query: {query}\nFile Path: {file_path}")
        ]
    }
    logging.info("Starting research graph with test input")
    asyncio.run(run_research_graph(test_input))
    logging.info("Research graph completed")