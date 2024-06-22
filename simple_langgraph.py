import operator
from typing import Annotated, TypedDict, Union

from colorama import Fore, Style
from langchain import hub
from langchain.agents import create_openai_functions_agent
from langchain_core.agents import AgentAction, AgentActionMessageLog, AgentFinish
from langchain_core.messages import BaseMessage
from langchain_core.runnables.base import Runnable
from langchain_openai.chat_models import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt.tool_executor import ToolExecutor

from setup_environment import set_environment_variables
from tools import generate_image, get_weather

from io import BytesIO
# from IPython.display import Image, display
import graphviz

set_environment_variables("LangGraph Basics")

LLM = ChatOpenAI(model="gpt-3.5-turbo-0125", streaming=True)
TOOLS = [get_weather, generate_image]
# https://smith.langchain.com/hub/hwchase17
PROMPT = hub.pull("hwchase17/openai-functions-agent")

class AgentState(TypedDict):
    input: str
    chat_history: list[BaseMessage]
    agent_outcome: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

# All Runnable type objects have the invoke, stream, and batch methods
runnable_agent: Runnable = create_openai_functions_agent(LLM, TOOLS, PROMPT)

# inputs = {
#     "input": "give me the weather for New York please.",
#     "chat_history": [],
#     "intermediate_steps": [],
# }

# agent_outcome = runnable_agent.invoke(inputs)
# print(agent_outcome)

def agent_node(input: AgentState):
    agent_outcome: AgentActionMessageLog = runnable_agent.invoke(input)
    return {"agent_outcome": agent_outcome}

tool_executor = ToolExecutor(TOOLS)

# We extract the agent_action from the input dictionary and then call the invoke method on the tool_executor object which will run whatever tool the agent wants to call for us.
# We have a print statement just for our own visual feedback here, and then we return the intermediate_steps list with the agent_action and the output of the tool call. Notice that this is the intermediate steps list that we defined in the AgentState object and talked about earlier and will be added to whatever steps were already there.
def tool_executor_node(input: AgentState):
    agent_action = input["agent_outcome"]
    output = tool_executor.invoke(agent_action)
    print(f"Executed {agent_action} with output: {output}")
    return {"intermediate_steps": [(agent_action, output)]}

# if the agent_outcome is an instance of AgentFinish we return "END" to signal that the graph is done, otherwise, we return "continue" to signal that the graph should continue.
def continue_or_end_test(data: AgentState):
    if isinstance(data["agent_outcome"], AgentFinish):
        return "END"
    else:
        return "continue"
    
# First, we instantiate a new StateGraph passing in our AgentState object that we defined. We then simply add our two nodes, giving them a string name and passing in the functions we wrote second. Lastly, we set the entry point to the agent node, which is the first node that will be called when we start the graph.    
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tool_executor", tool_executor_node)

workflow.set_entry_point("agent")

workflow.add_edge("tool_executor", "agent")

workflow.add_conditional_edges(
    "agent", continue_or_end_test, {"continue": "tool_executor", "END": END}
)

weather_app = workflow.compile()

# def displayGraph(chain, chain_selection="default graph"):
#     # Display the graph visualization
#     # display(Image(chain.get_graph(xray=True).draw_mermaid_png()))
#     graph = chain.get_graph(xray=True)
#     png_bytes = graph.draw_png()
    
#     # Create a graphviz instance from the PNG bytes
#     graphviz_graph = graphviz.Source(bytestring=png_bytes)
    
#     # Print the graph in the terminal
#     print(graphviz_graph.source)
#     # graph = chain.get_graph(xray=True)
#     # mermaid_png = graph.draw_mermaid_png()
#     # png_bytes = BytesIO(mermaid_png)
#     # st.image(png_bytes, caption=chain_selection, use_column_width=True)

# displayGraph(weather_app)

def call_weather_app(query: str):
    inputs = {"input": query, "chat_history": []}
    output = weather_app.invoke(inputs)
    result = output.get("agent_outcome").return_values["output"]  # type: ignore
    steps = output.get("intermediate_steps")

    print(f"{Fore.BLUE}Result: {result}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Steps: {steps}{Style.RESET_ALL}")

# call_weather_app("What is the weather in Shanghai?")
# call_weather_app("What is the weather in New York?")

call_weather_app("Give me a visual image displaying the current weather in Glasgow, UK. With the temperature figure showing at the bottom of the image")