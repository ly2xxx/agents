from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from typing import Annotated
from pydantic import BaseModel, Field
from langchain.tools import tool

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# LLM = ChatOpenAI(
#                 model="llama3.2", base_url="http://localhost:11434/v1", temperature=0
#             )
LLM = ChatOllama(model="llama3.2", temperature=0)

class ChatInput(BaseModel):
    # messages: Annotated[list, add_messages] = Field(default_factory=list)
    query: str = Field(description="The question to be answered using LLM.")

@tool("chatbot", args_schema=ChatInput)
def chatbot(query: str, llm: BaseChatModel = LLM):
    """
    Process the current state and generate a response using the language model.
    
    Args:
        query: The current state containing messages and other information.
    
    Returns:
        dict: A dictionary containing the updated messages with the model's response.
    """
    # return {"messages": [llm.invoke(state["messages"])]}
    return {"messages": [llm.invoke(query)]}

if __name__ == "__main__":
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            
            # Call the chatbot function with the user input
            response = chatbot.invoke(user_input)
            
            print("Assistant:", response["messages"][-1].content)
        except Exception as e:
            print(f"An error occurred: {e}")
            break
