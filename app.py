import streamlit as st
from langchain_core.messages import HumanMessage
from multi_agent import travel_agent_graph
from web_research import research_graph
from io import BytesIO

TRAVEL_AGENT = "Travel Agency"
RESEARCH_AGENT = "Research Assistant"

def main():
    st.title("Multi-agent Assistant Demo")

    chain_selection = st.selectbox("Select assistant", [TRAVEL_AGENT, RESEARCH_AGENT])

    langgraph_chain = None
    if chain_selection == TRAVEL_AGENT:
        langgraph_chain = travel_agent_graph
    elif chain_selection == RESEARCH_AGENT:
        langgraph_chain = research_graph
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
        for chunk in langgraph_chain.stream({"messages": [HumanMessage(content=user_input)]}):
            if "__end__" not in chunk:
                st.write(chunk)
                st.write("---")

def displayGraph(chain, chain_selection):
    # Display the graph visualization
    graph = chain.get_graph(xray=True)
    mermaid_png = graph.draw_mermaid_png()
    png_bytes = BytesIO(mermaid_png)
    st.image(png_bytes, caption=chain_selection, use_column_width=True)

if __name__ == "__main__":
    main()