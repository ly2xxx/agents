import streamlit as st
from langchain_core.messages import HumanMessage
from multi_agent import travel_agent_graph
from io import BytesIO

def main():
    st.title("Multi-agent Assistant Demo")

    displayGraph(travel_agent_graph, "Travel Agent")

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
        for chunk in travel_agent_graph.stream({"messages": [HumanMessage(content=user_input)]}):
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