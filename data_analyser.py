# import asyncio
# import functools
# import operator
# import uuid

# from typing import Annotated, Sequence, TypedDict

# from langchain.agents import AgentExecutor, create_openai_tools_agent
# from langchain_community.tools.tavily_search import TavilySearchResults
# from langchain_core.messages import BaseMessage, HumanMessage
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# # from langchain_openai import ChatOpenAI
# # from langgraph.graph import END, StateGraph

# from tools import *

# from tools.pdf import OUTPUT_DIRECTORY
# from tools.web import research
# from web_research_prompts import RESEARCHER_SYSTEM_PROMPT, TAVILY_AGENT_SYSTEM_PROMPT, RAG_SYSTEM_PROMPT

import os
import logging
from setup_environment import set_environment_variables
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph,END,START
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from tools.state import State
from tools.node import agent_node,human_choice_node,note_agent_node,human_review_node,refiner_node
from tools.create_agent import create_agent,create_supervisor,create_note_agent
from tools.router import QualityReview_router,hypothesis_router,process_router
from tools.internet import google_search,FireCrawl_scrape_webpages
from tools.basetool import execute_code,execute_command
from tools.FileEdit import create_document,read_document,edit_document,collect_data
from langchain.agents import load_tools
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from data_analyser_prompts import HYPOTHESIS_AGENT_SYSTEM_PROMPT, RESEARCH_SUPERVISOR_SYSTEM_PROMPT, VISUALIZATION_AGENT_SYSTEM_PROMPT, CODE_AGENT_SYSTEM_PROMPT, WEB_SEARCH_AGENT_SYSTEM_PROMPT, REPORT_WRITER_AGENT_SYSTEM_PROMPT, QUALITY_REVIEW_AGENT_SYSTEM_PROMPT, NOTE_TAKER_AGENT_SYSTEM_PROMPT, REFINER_AGENT_SYSTEM_PROMPT
from colorama import Fore, Style

# class AgentState(TypedDict):
#     messages: Annotated[Sequence[BaseMessage], operator.add]

class DataAnalyzerGraph:
    def __init__(self):
        set_environment_variables("Data_Analyzer_Graph")
        # self.TAVILY_TOOL = TavilySearchResults(max_results=6)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=4096)
        
        self.json_llm = ChatOpenAI(
            model="gpt-4o-mini",
            model_kwargs={"response_format": {"type": "json_object"}},
            temperature=0,
            max_tokens=4096
        )
        logging.info("Language models initialized successfully.")

    def create_graph(self):
        WORKING_DIRECTORY = os.getenv('WORKING_DIRECTORY', './data_storage/')
        workflow = StateGraph(State)
        members = ["Hypothesis","Process","Visualization", "Search", "Coder", "Report", "QualityReview","Refiner"]
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        #works
        hypothesis_agent = create_agent(
            self.llm, 
            [collect_data,wikipedia,google_search,FireCrawl_scrape_webpages]+load_tools(["arxiv"],),
            HYPOTHESIS_AGENT_SYSTEM_PROMPT,
            members, WORKING_DIRECTORY)
        #works {'next': 'Search'}
        process_agent = create_supervisor(
            self.llm,
            RESEARCH_SUPERVISOR_SYSTEM_PROMPT,
            ["Visualization", "Search", "Coder", "Report"],
        )
        #Error: [WinError 3] The system cannot find the path specified
        visualization_agent = create_agent(
            self.llm, 
            [read_document, execute_code, execute_command],
            VISUALIZATION_AGENT_SYSTEM_PROMPT,
            members,WORKING_DIRECTORY
            )
        
        code_agent = create_agent(
            self.llm,
            [read_document,execute_code, execute_command],
            CODE_AGENT_SYSTEM_PROMPT,
            members,WORKING_DIRECTORY
        )
        #works
        searcher_agent= create_agent(
            self.llm,
            [read_document, collect_data,wikipedia,google_search,FireCrawl_scrape_webpages]+load_tools(["arxiv"],),
            WEB_SEARCH_AGENT_SYSTEM_PROMPT,
            members,WORKING_DIRECTORY
        )

        report_agent = create_agent(
            self.llm, 
            [create_document, read_document, edit_document], 
            REPORT_WRITER_AGENT_SYSTEM_PROMPT,
            members,WORKING_DIRECTORY
        )
        #works
        quality_review_agent=create_agent(
            self.llm, 
            [create_document,read_document,edit_document], 
            QUALITY_REVIEW_AGENT_SYSTEM_PROMPT,
            members,WORKING_DIRECTORY
        )
        #Error parsing output: Agent stopped due to iteration limit or time limit.
        note_agent=create_note_agent(
            self.json_llm, 
            [read_document], 
            NOTE_TAKER_AGENT_SYSTEM_PROMPT,
        )

        refiner_agent = create_agent(
            self.llm,  
            [read_document, edit_document,create_document,collect_data,wikipedia,google_search,FireCrawl_scrape_webpages]+load_tools(["arxiv"],),
            REFINER_AGENT_SYSTEM_PROMPT,
            members,  
            WORKING_DIRECTORY
        )

        workflow.add_node("Hypothesis", lambda state: agent_node(state, hypothesis_agent, "hypothesis_agent"))
        workflow.add_node("Process", lambda state: agent_node(state, process_agent, "process_agent"))
        workflow.add_node("Visualization", lambda state: agent_node(state, visualization_agent, "visualization_agent"))
        workflow.add_node("Search", lambda state: agent_node(state, searcher_agent, "searcher_agent"))
        workflow.add_node("Coder", lambda state: agent_node(state, code_agent, "code_agent"))
        workflow.add_node("Report", lambda state: agent_node(state, report_agent, "report_agent"))
        workflow.add_node("QualityReview", lambda state: agent_node(state, quality_review_agent, "quality_review_agent"))
        workflow.add_node("NoteTaker", lambda state: note_agent_node(state, note_agent, "note_agent"))
        workflow.add_node("HumanChoice", human_choice_node)
        workflow.add_node("HumanReview", human_review_node)
        workflow.add_node("Refiner", lambda state: refiner_node(state, refiner_agent, "refiner_agent"))

        workflow.add_edge("Hypothesis", "HumanChoice")
        workflow.add_conditional_edges(
            "HumanChoice",
            hypothesis_router,
            {
                "Hypothesis": "Hypothesis",
                "Process": "Process"
            }
        )

        workflow.add_conditional_edges(
            "Process",
            process_router,
            {
                "Coder": "Coder",
                "Search": "Search",
                "Visualization": "Visualization",
                "Report": "Report",
                "Process": "Process",
                "Refiner": "Refiner",
            }
        )

        for member in ["Visualization",'Search','Coder','Report']:
            workflow.add_edge(member, "QualityReview")

        workflow.add_conditional_edges(
            "QualityReview",
            QualityReview_router,
            {
                'Visualization': "Visualization",
                'Search': "Search",
                'Coder': "Coder",
                'Report': "Report",
                'NoteTaker': "NoteTaker",
            }
        )
        workflow.add_edge("NoteTaker", "Process")

        workflow.add_edge("Refiner", "HumanReview")

        # Add an edge from HumanReview to Process
        workflow.add_conditional_edges(
            "HumanReview",
            lambda state: "Process" if state and state.get("needs_revision", False) else "END",
            {
                "Process": "Process",
                "END": END
            }
        )

        workflow.add_edge(START, "Hypothesis")
        memory = MemorySaver()
        
        return workflow.compile()


# Usage
web_research = DataAnalyzerGraph()
graph = web_research.create_graph()

if __name__ == "__main__":
    userInput = '''
    datapath:Your data set name
    Use machine learning to perform data analysis and write complete graphical reports
    Research Barclays share price and predict future trends
    '''

    for chunk in graph.stream(
            {
            "messages": [
                HumanMessage(
                    content=userInput
                ),
            ],
            "hypothesis": "",
            "process_decision":"",
            "process": "",
            "visualization_state": "",
            "searcher_state": "",
            "code_state": "",
            "report_section": "",
            "quality_review": "",
            "needs_revision": False,
            "last_sender": "",
        },
        {"configurable": {"thread_id": "1"}, "recursion_limit": 3000},
        stream_mode="values",
        debug=False
    ):
        if "__end__" not in chunk:
            print(chunk)
            print(f"{Fore.GREEN}#############################{Style.RESET_ALL}")
