# import asyncio
# import operator
# from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph import MessagesState
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
# from langgraph.checkpoint.memory import MemorySaver
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
# import aiosqlite
# from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver

from setup_environment import set_environment_variables

class State(MessagesState):
    summary: str

class RAGResearchChatbot:
    def __init__(self, llm=None):
        # db_path = "state_db/example.db"
        # self.CONN = sqlite3.connect(db_path, check_same_thread=False)
        # In memory
        self.CONN = sqlite3.connect(":memory:", check_same_thread = False)
        set_environment_variables("RAG_Research_Chatbot")
        self.LLM = llm if llm else ChatOpenAI(model="gpt-4o-mini")
        
        self.CONVERSATION_NODE_NAME = "conversation"
        self.SUMMARIZE_NODE_NAME = "summarize_conversation"

    def call_model(self, state: State):
        summary = state.get("summary", "")
        if summary:
            system_message = f"Summary of conversation earlier: {summary}"
            messages = [SystemMessage(content=system_message)] + state["messages"]
        else:
            messages = state["messages"]
        
        response = self.LLM.invoke(messages)
        return {"messages": [response]}

    def summarize_conversation(self, state: State):
        summary = state.get("summary", "")
        if summary:
            summary_message = (
                f"This is summary of the conversation to date: {summary}\n\n"
                "Extend the summary by taking into account the new messages above:"
            )
        else:
            summary_message = "Create a summary of the conversation above:"

        messages = state["messages"] + [HumanMessage(content=summary_message)]
        response = self.LLM.invoke(messages)
        
        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
        return {"summary": response.content, "messages": delete_messages}

    def should_continue(self, state: State):
        messages = state["messages"]
        if len(messages) > 3:
            return self.SUMMARIZE_NODE_NAME
        return END

    def create_rag_research_chatbot_graph(self):
        workflow = StateGraph(State)
        
        workflow.add_node(self.CONVERSATION_NODE_NAME, self.call_model)
        workflow.add_node(self.SUMMARIZE_NODE_NAME, self.summarize_conversation)

        workflow.add_edge(START, self.CONVERSATION_NODE_NAME)
        workflow.add_conditional_edges(self.CONVERSATION_NODE_NAME, self.should_continue)
        workflow.add_edge(self.SUMMARIZE_NODE_NAME, self.CONVERSATION_NODE_NAME)

        memory = SqliteSaver(self.CONN)
        return workflow.compile(checkpointer=memory)

# Usage
rag_research_chatbot = RAGResearchChatbot()
chatbot_graph = rag_research_chatbot.create_rag_research_chatbot_graph()

# Run the graph
# async def run_chatbot_graph(graph, input):
#     async for output in graph.astream(input):
#         for node_name, output_value in output.items():
#             print("---")
#             print(f"Output from node '{node_name}':")
#             print(output_value)
#         print("\n---\n")
def run_chatbot_graph(graph, input, config):
    output = graph.invoke(input, config=config)
    if isinstance(output, str):
        print("---")
        print("Output:")
        print(output)
    else:
        for node_name, output_value in output.items():
            print("---")
            print(f"Output from node '{node_name}':")
            print(output_value)
    print("\n---\n")

if __name__ == "__main__":
    chatbot_graph = rag_research_chatbot.create_rag_research_chatbot_graph()
    state = {"messages": []}
    config = {"configurable": {"thread_id": "1"}}

    print("Welcome to the RAG Research Chatbot. Type 'exit' to end the conversation.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        
        state["messages"].append(HumanMessage(content=user_input))
        run_chatbot_graph(chatbot_graph, {"messages": state["messages"]}, config)
        
        # Extract the last message from the state
        if state["messages"]:
            last_message = state["messages"][-1]
            print(f"Chatbot: {last_message.content}")
    
    print("Thank you for using the RAG Research Chatbot!")

