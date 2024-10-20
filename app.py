import streamlit as st
from langchain_core.messages import HumanMessage
from multi_agent import create_travel_agent_graph
# from web_research import create_web_research_graph
# from web_research_rag import create_web_research_rag_graph
from web_research_consolidated import WebResearchGraph
from rag_research_chatbot import RAGResearchChatbot
from io import BytesIO
from PIL import Image
import asyncio
import tempfile
import os
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from ui.file_picker import render_file_picker

TRAVEL_AGENT = "Travel Agency"
RESEARCH_AGENT = "Research Assistant"
RAG_RESEARCH_AGENT = "RAG Research Assistant"
RAG_CHATBOT_AGENT = "RAG Chatbot Agent"
SUPPORT_TYPES = ["pdf", "txt", "md"]

def process_uploaded_files(uploaded_files, support_types):
    temp_file_paths = []
    suffixes = ['.' + file_type for file_type in support_types]
    
    for uploaded_file in uploaded_files:
        file_suffix = os.path.splitext(uploaded_file.name)[1].lower()
        if file_suffix in suffixes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_paths.append(temp_file.name)
        else:
            st.warning(f"File type {file_suffix} not supported. Supported types: {','.join(support_types)}")
    
    return temp_file_paths

def main():
    st.title("Multi-agent Assistant Demo")

    model_selection = st.selectbox("Select LLM model", ["gpt-4o-mini", "llama3.2"])
    if model_selection == "gpt-4o-mini":
        llm = ChatOpenAI(model=model_selection, temperature=0)
    else:
        llm = ChatOllama(model=model_selection, temperature=0)
        llm_travel = ChatOpenAI(model=model_selection, base_url="http://localhost:11434/v1", temperature=0)

    chain_selection = st.selectbox("Select assistant", [TRAVEL_AGENT, RESEARCH_AGENT, RAG_RESEARCH_AGENT, RAG_CHATBOT_AGENT])
    web_research = WebResearchGraph(llm)
    rag_chatbot = RAGResearchChatbot(llm)

    langgraph_chain = None
    if chain_selection == TRAVEL_AGENT:
        langgraph_chain = create_travel_agent_graph()
    elif chain_selection == RESEARCH_AGENT:
        langgraph_chain = web_research.create_web_research_graph()
    elif chain_selection == RAG_RESEARCH_AGENT:
        langgraph_chain = web_research.create_web_research_rag_graph()
    elif chain_selection == RAG_CHATBOT_AGENT:
        langgraph_chain = rag_chatbot.create_rag_research_chatbot_graph()
    else:
        langgraph_chain = None
    
    displayGraph(langgraph_chain, chain_selection)

    # Get user input
    user_input = st.text_area("Enter your query:")

    # Create a placeholder
    dynamic_content_container = st.empty()
    # File picker (only shown for RAG_RESEARCH_AGENT)
    if chain_selection in [RAG_RESEARCH_AGENT, RAG_CHATBOT_AGENT]:#== RAG_RESEARCH_AGENT or RAG_CHATBOT_AGENT:
        with dynamic_content_container.container():
            uploaded_files = render_file_picker(SUPPORT_TYPES)
    else:
        dynamic_content_container.empty()
        # uploaded_files = []
        # num_files = st.number_input("Pick your file(s) - files for Retrieval Augmented Query", min_value=1, value=1, step=1)
        # for i in range(num_files):
        #     file = st.file_uploader(f"Choose file {i+1}", type=SUPPORT_TYPES, key=f"file_{i}")
        #     if file:
        #         uploaded_files.append(file)

    if st.button("Submit"):
        temp_file_paths = []  # Initialize the list here
        query = {"messages": [HumanMessage(content=user_input)]}
        if chain_selection == TRAVEL_AGENT:
            for chunk in langgraph_chain.stream(query):
                if "__end__" not in chunk:
                    st.write(chunk)
                    st.write("---")
        elif chain_selection == RESEARCH_AGENT:
            asyncio.run(run_research_graph(query, langgraph_chain))
        elif chain_selection == RAG_RESEARCH_AGENT:
            # # Save all uploaded files to temporary locations
            # temp_file_paths = []
            # suffixes = ['.' + file_type for file_type in SUPPORT_TYPES]
            # for uploaded_file in uploaded_files:
            #     file_suffix = os.path.splitext(uploaded_file.name)[1].lower()
            #     if file_suffix in suffixes:
            #         with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as temp_file:
            #             temp_file.write(uploaded_file.read())
            #             temp_file_paths.append(temp_file.name)
            #     else:
            #         st.warning(f"File type {file_suffix} not supported. Supported types: {','.join(SUPPORT_TYPES)}")

            # Convert the list of file paths to a comma-delimited string
            temp_file_paths = process_uploaded_files(uploaded_files, SUPPORT_TYPES)#','.join(temp_file_paths)
            # Use the temporary file path in the function call
            asyncio.run(run_research_graph({"messages": [HumanMessage(content=f"Query: {user_input}\nFile Path: {','.join(temp_file_paths)}")]}, langgraph_chain))
        elif chain_selection == RAG_CHATBOT_AGENT:
            config = {"configurable": {"thread_id": "1"}}  # Add a thread_id
            temp_file_paths = process_uploaded_files(uploaded_files, SUPPORT_TYPES)
            input_data = {"messages": [HumanMessage(content=f"Query: {user_input}\nFile Path: {','.join(temp_file_paths)}")]}
            run_chatbot_graph(langgraph_chain, input_data, config)

        # Clean up the temporary files after use
        for path in temp_file_paths:
            os.unlink(path)

def displayGraph(chain, chain_selection):
    # Display the graph visualization
    graph = chain.get_graph(xray=True)
    mermaid_png = graph.draw_mermaid_png()
    png_bytes = BytesIO(mermaid_png)
    image = Image.open(png_bytes)

    new_height = 460  # Desired width in pixels
    new_width = int(new_height * image.width / image.height)  # Maintain aspect ratio
    new_image = image.resize((new_width, new_height))
    st.image(new_image, caption=chain_selection)#, use_column_width=True)

async def run_research_graph(input, chain):
    async for output in chain.astream(input):
        for node_name, output_value in output.items():
            st.write("---")
            st.write(f"Output from node '{node_name}':")
            if isinstance(output_value, dict) and 'messages' in output_value:
                for message in output_value['messages']:
                    st.markdown(message.content, unsafe_allow_html=True)
            else:
                st.write(output_value)
        st.write("\n---\n")

def run_chatbot_graph(graph, input, config):
    output = graph.invoke(input, config=config)
    if isinstance(output, str):
        st.write("---")
        st.write("Output:")
        st.write(output)
    else:
        for node_name, output_value in output.items():
            st.write("---")
            st.write(f"Output from node '{node_name}':")
            st.write(output_value)
    st.write("\n---\n")


if __name__ == "__main__":
    main()