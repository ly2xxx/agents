import streamlit as st
from langchain_core.messages import HumanMessage
from multi_agent import travel_agent_graph
from web_research import create_web_research_graph
from io import BytesIO
from PIL import Image
import asyncio

TRAVEL_AGENT = "Travel Agency"
RESEARCH_AGENT = "Research Assistant"

def main():
    st.title("Multi-agent Assistant Demo")

    chain_selection = st.selectbox("Select assistant", [TRAVEL_AGENT, RESEARCH_AGENT])

    langgraph_chain = None
    if chain_selection == TRAVEL_AGENT:
        langgraph_chain = travel_agent_graph
    elif chain_selection == RESEARCH_AGENT:
        langgraph_chain = create_web_research_graph()
    else:
        langgraph_chain = None
    
    displayGraph(langgraph_chain, chain_selection)

    # Get user input
    user_input = st.text_area("Enter your query:")

    # File picker
    uploaded_files = []
    num_files = st.number_input("Pick your file(s) - Number of files to upload", min_value=1, value=1, step=1)
    for i in range(num_files):
        file = st.file_uploader(f"Choose file {i+1}", type=["pdf", "txt", "docx"], key=f"file_{i}")
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