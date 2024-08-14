import streamlit as st
from langchain_core.messages import HumanMessage
from multi_agent import create_travel_agent_graph
from web_research import create_web_research_graph
from web_research_rag import create_web_research_rag_graph
from io import BytesIO
from PIL import Image
import asyncio
import tempfile
import os

TRAVEL_AGENT = "Travel Agency"
RESEARCH_AGENT = "Research Assistant"
RAG_RESEARCH_AGENT = "RAG Research Assistant"

def main():
    st.title("Multi-agent Assistant Demo")

    chain_selection = st.selectbox("Select assistant", [TRAVEL_AGENT, RESEARCH_AGENT, RAG_RESEARCH_AGENT])

    langgraph_chain = None
    if chain_selection == TRAVEL_AGENT:
        langgraph_chain = create_travel_agent_graph()
    elif chain_selection == RESEARCH_AGENT:
        langgraph_chain = create_web_research_graph()
    elif chain_selection == RAG_RESEARCH_AGENT:
        langgraph_chain = create_web_research_rag_graph()
    else:
        langgraph_chain = None
    
    displayGraph(langgraph_chain, chain_selection)

    # Get user input
    user_input = st.text_area("Enter your query:")

    # File picker (only shown for RAG_RESEARCH_AGENT)
    if chain_selection == RAG_RESEARCH_AGENT:
        uploaded_files = []
        num_files = st.number_input("Pick your file(s) - Number of files to upload", min_value=1, value=1, step=1)
        for i in range(num_files):
            file = st.file_uploader(f"Choose file {i+1}", type=["pdf", "txt", "md"], key=f"file_{i}")
            if file:
                uploaded_files.append(file)

    if st.button("Submit"):
        query = {"messages": [HumanMessage(content=user_input)]}
        if chain_selection == TRAVEL_AGENT:
            for chunk in langgraph_chain.stream(query):
                if "__end__" not in chunk:
                    st.write(chunk)
                    st.write("---")
        elif chain_selection == RESEARCH_AGENT:
            asyncio.run(run_research_graph(query, langgraph_chain))
        elif chain_selection == RAG_RESEARCH_AGENT:
            # Save all uploaded files to temporary locations
            temp_file_paths = []
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(uploaded_file.read())
                    temp_file_paths.append(temp_file.name)

            # Convert the list of file paths to a comma-delimited string
            temp_file_path = ','.join(temp_file_paths)
            # Use the temporary file path in the function call
            asyncio.run(run_research_graph({"messages": [HumanMessage(content=f"Query: {user_input}\nPDF Path: {temp_file_path}")]}, langgraph_chain))
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
            st.write(output_value)
        st.write("\n---\n")

if __name__ == "__main__":
    main()