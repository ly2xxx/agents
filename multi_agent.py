import functools
import operator
from typing import Annotated, Sequence, TypedDict

from colorama import Fore, Style
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from setup_environment import set_environment_variables
from tools import * #generate_image, markdown_to_pdf_file

#... all the other imports ...
#... all the other imports ...

from multi_agent_prompts import (
    TEAM_SUPERVISOR_SYSTEM_PROMPT,
    TRAVEL_AGENT_SYSTEM_PROMPT,
    LANGUAGE_ASSISTANT_SYSTEM_PROMPT,
    VISUALIZER_SYSTEM_PROMPT,
    DESIGNER_SYSTEM_PROMPT,
)

set_environment_variables("Multi_Agent_Team")

TRAVEL_AGENT_NAME = "travel_agent"
LANGUAGE_ASSISTANT_NAME = "language_assistant"
VISUALIZER_NAME = "visualizer"
DESIGNER_NAME = "designer"

TEAM_SUPERVISOR_NAME = "team_supervisor"
MEMBERS = [TRAVEL_AGENT_NAME, LANGUAGE_ASSISTANT_NAME, VISUALIZER_NAME]
OPTIONS = ["FINISH"] + MEMBERS

TAVILY_TOOL = TavilySearchResults()
LLM = ChatOpenAI(model="gpt-4o-mini-2024-07-18")

# We define a function named create_agent which takes an llm of the type BaseChatModel. This is just a type hint but it was part of our imports for clarity. BaseChatModel is the base class for all chat models in LangChain, including the ChatOpenAI variation we use here. You can pass any LLM you want and have different nodes of the same graph run on completely different LLMs. The other arguments are a list of tools and a system_prompt string.
def create_agent(llm: BaseChatModel, tools: list, system_prompt: str):
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_openai_tools_agent(llm, tools, prompt_template)
    # This AgentExecutor comes with LangChain and will basically combine the agent and the executor nodes we had in the previous part into a single node, handling the function call logic we did in the previous part for us! It takes an agent and a list of tools for that agent to use as arguments.
    agent_executor = AgentExecutor(agent=agent, tools=tools)  # type: ignore
    return agent_executor

# This time we need two entries. The first is the messages which is a sequence of BaseMessage objects which again are just messages like ("human", "Hello, how are you doing?"), or ("ai", "I'm doing well, thanks!"),. We define it as a Sequence, so like a list or a tuple of these messages, and the operator.add again indicates that we will add to this sequence of messages with each step. Annotated is just used as it allows us to add the annotation of operator.add.
# The second entry is the next which is a string that will be the name of the next agent to call. This is the agent that the team_supervisor will decide to call next based on the state object it receives and then we can use this field to see which agent to route to next. This field can just be overwritten as we don’t need the history, so a single string without any fancy annotations will do fine here.
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# The function takes the state object, an agent, and the string name for the agent (the ones we defined up top as constants). 
# Then we simply need to invoke the agent with the state and then keeping with the promise we made above in the AgentState object we defined the node needs to return a messages object with a message in it. We will simply use a HumanMessage, as it doesn’t really matter who the message comes from, and get the result from result["output"] which is the output of the agent’s call.
def agent_node(state, agent, name):
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}

def create_travel_agent_graph():
    router_function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "next",
                    "anyOf": [
                        {"enum": OPTIONS},
                    ],
                }
            },
            "required": ["next"],
        },
    }

    # The first is the TEAM_SUPERVISOR_SYSTEM_PROMPT we defined in the multi_agent_prompts.py file. 
    # The second is a MessagesPlaceholder for the messages variable 
    # and the third is a short system message that reminds the team supervisor what it’s task is and what options it has available to choose from.
    # we use the join method on the OPTIONS and MEMBERS lists to turn them into a single string with the members separated by a comma and a space as we cannot pass list variables to LLMs.
    team_supervisor_prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", TEAM_SUPERVISOR_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}",
            ),
        ]
    ).partial(options=", ".join(OPTIONS), members=", ".join(MEMBERS))

    # So we simply define the team_supervisor_chain as the prompt template we just made for it, then we pipe that into the LLM, and pipe that into a JsonOutputFunctionsParser. As we’re using a function here we can use the JSON output parser to extract the next property from the arguments the LLM provides for us.
    team_supervisor_chain = (
        team_supervisor_prompt_template
        | LLM.bind_functions(functions=[router_function_def], function_call="route")
        | JsonOutputFunctionsParser()
    )

    travel_agent = create_agent(LLM, [TAVILY_TOOL], TRAVEL_AGENT_SYSTEM_PROMPT)
    # To get the travel agent’s node we need to use the agent_node function we defined before, which needs three arguments, the agent, the state and the name of the agent in string format. We have the agent and the name already, but the state will only be available at runtime. To solve this problem we can use the functools.partial function to create a new function that has the agent and name already filled in, and then we can pass in the state at runtime.
    travel_agent_node = functools.partial(
        agent_node, agent=travel_agent, name=TRAVEL_AGENT_NAME
    )

    language_assistant = create_agent(LLM, [TAVILY_TOOL], LANGUAGE_ASSISTANT_SYSTEM_PROMPT)
    language_assistant_node = functools.partial(
        agent_node, agent=language_assistant, name=LANGUAGE_ASSISTANT_NAME
    )

    visualizer = create_agent(LLM, [generate_image], VISUALIZER_SYSTEM_PROMPT)
    visualizer_node = functools.partial(agent_node, agent=visualizer, name=VISUALIZER_NAME)

    designer = create_agent(LLM, [markdown_to_pdf_file], DESIGNER_SYSTEM_PROMPT)
    designer_node = functools.partial(agent_node, agent=designer, name=DESIGNER_NAME)

    workflow = StateGraph(AgentState)
    workflow.add_node(TRAVEL_AGENT_NAME, travel_agent_node)
    workflow.add_node(LANGUAGE_ASSISTANT_NAME, language_assistant_node)
    workflow.add_node(VISUALIZER_NAME, visualizer_node)
    workflow.add_node(DESIGNER_NAME, designer_node)
    workflow.add_node(TEAM_SUPERVISOR_NAME, team_supervisor_chain)

    for member in MEMBERS:
        workflow.add_edge(member, TEAM_SUPERVISOR_NAME)

    workflow.add_edge(DESIGNER_NAME, END)

    conditional_map = {name: name for name in MEMBERS}
    conditional_map["FINISH"] = DESIGNER_NAME
    workflow.add_conditional_edges(
        TEAM_SUPERVISOR_NAME, lambda x: x["next"], conditional_map
    )

    workflow.set_entry_point(TEAM_SUPERVISOR_NAME)

    travel_agent_graph = workflow.compile()
    return travel_agent_graph

travel_agent_graph = create_travel_agent_graph()

if __name__ == "__main__":
    for chunk in travel_agent_graph.stream(
        {"messages": [HumanMessage(content="I want to go to St Andrews for a weekend golf trip")]}, config={"recursion_limit": 50}
    ):
        if "__end__" not in chunk:
            print(chunk)
            print(f"{Fore.GREEN}#############################{Style.RESET_ALL}")