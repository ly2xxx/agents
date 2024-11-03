import streamlit as st
from langchain_core.messages import HumanMessage
from multi_agent import create_travel_agent_graph
# from web_research import create_web_research_graph
# from web_research_rag import create_web_research_rag_graph
from web_research_consolidated import WebResearchGraph
from rag_research_chatbot import RAGResearchChatbot
from mm_agent import ArticleWriterStateMachine
from io import BytesIO
from PIL import Image
import asyncio
import tempfile
import os
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from ui.file_picker import render_file_picker
import urllib.parse

TRAVEL_AGENT = "Travel Agency"
RESEARCH_AGENT = "Research Assistant"
RAG_RESEARCH_AGENT = "RAG Research Assistant"
RAG_CHATBOT_AGENT = "RAG Chatbot Agent"
ARTICLE_WRITER = "Article Writer"
SUPPORT_TYPES = ["pdf", "txt", "md", "xlsx"]
CHAIN_MODEL_OPTIONS = {
    TRAVEL_AGENT: ["gpt-4o-mini"],
    RESEARCH_AGENT: ["gpt-4o-mini", "llama3.2"],
    RAG_RESEARCH_AGENT: ["gpt-4o-mini", "llama3.2"],
    RAG_CHATBOT_AGENT: ["gpt-4o-mini", "llama3.2"],
    ARTICLE_WRITER: ["gpt-4o-mini"]
}

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

    chain_selection = st.selectbox("Select assistant", [TRAVEL_AGENT, RESEARCH_AGENT, RAG_RESEARCH_AGENT, RAG_CHATBOT_AGENT, ARTICLE_WRITER])
    
    # Clear chat history when switching away from RAG Chatbot Agent
    if "previous_agent" not in st.session_state:
        st.session_state.previous_agent = chain_selection
    elif st.session_state.previous_agent != chain_selection:
        if "chat_history" in st.session_state:
            del st.session_state.chat_history
        st.session_state.previous_agent = chain_selection

    # Get available models for the selected chain
    available_models = CHAIN_MODEL_OPTIONS.get(chain_selection, ["gpt-4o-mini", "llama3.2"])
    model_selection = st.selectbox("Select LLM model", available_models)
    if model_selection == "gpt-4o-mini":
        llm = ChatOpenAI(model=model_selection, temperature=0)
    else:
        llm = ChatOllama(model=model_selection, temperature=0)
        llm_travel = ChatOpenAI(model=model_selection, base_url="http://localhost:11434/v1", temperature=0)
    web_research = WebResearchGraph(llm)
    rag_chatbot = RAGResearchChatbot(llm)
    article_writer = ArticleWriterStateMachine()

    langgraph_chain = None
    if chain_selection == TRAVEL_AGENT:
        langgraph_chain = create_travel_agent_graph()
    elif chain_selection == RESEARCH_AGENT:
        langgraph_chain = web_research.create_web_research_graph()
    elif chain_selection == RAG_RESEARCH_AGENT:
        langgraph_chain = web_research.create_web_research_rag_graph()
    elif chain_selection == RAG_CHATBOT_AGENT:
        langgraph_chain = rag_chatbot.create_rag_research_chatbot_graph()
    elif chain_selection == ARTICLE_WRITER:
        langgraph_chain = article_writer.getGraph()
    else:
        langgraph_chain = None
    
    displayGraph(langgraph_chain, chain_selection)

    # Get user input
    user_input = st.text_area("Enter your query:", key=f"query_{chain_selection}")

    # Create a placeholder
    dynamic_content_container = st.empty()
    # File picker (only shown for RAG_RESEARCH_AGENT)
    if chain_selection in [RAG_RESEARCH_AGENT, RAG_CHATBOT_AGENT]:
        with dynamic_content_container.container():
            uploaded_files = render_file_picker(SUPPORT_TYPES)
    elif chain_selection in [ARTICLE_WRITER]:
        with dynamic_content_container.container():
            import mm_st
            mm_st.main()
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
        else:
            st.write("Feature under construction")

        # Clean up the temporary files after use
        for path in temp_file_paths:
            os.unlink(path)

    # Add this section to re-render chat history after page reloads
    if chain_selection == RAG_CHATBOT_AGENT and "chat_history" in st.session_state:
        render_chat_history_and_thoughts(st.session_state.chat_history)

def displayGraph(chain, chain_selection):
    # Add mermaid initialization scripts to the page
    st.markdown("""
        <script src="mermaid.min.js"></script>
        <script>mermaid.initialize({startOnLoad:true});</script>
    """, unsafe_allow_html=True)
    
    # Display the graph visualization
    graph = chain.get_graph(xray=True)
    mermaid_png = graph.draw_mermaid_png()
    png_bytes = BytesIO(mermaid_png)
    image = Image.open(png_bytes)

    new_height = 460  # Desired width in pixels
    new_width = int(new_height * image.width / image.height)  # Maintain aspect ratio
    new_image = image.resize((new_width, new_height))
    st.image(new_image, caption=chain_selection)

# def displayGraph(chain, chain_selection):
#     # Get the graph
#     graph = chain.get_graph(xray=True)
    
#     # Create Mermaid syntax with proper indentation
#     mermaid_lines = [
#         "            graph TD"
#     ]
    
#     # Add nodes with indentation
#     for node_id, node in graph.nodes.items():
#         mermaid_lines.append(f'            {node_id}["{node.name}"]')
    
#     # Add edges with indentation
#     for edge in graph.edges:
#         if edge.conditional and edge.data:
#             mermaid_lines.append(f'            {edge.source} -->|{edge.data}| {edge.target}')
#         else:
#             mermaid_lines.append(f'            {edge.source} --> {edge.target}')
    
#     mermaid_definition = "\n".join(mermaid_lines)

#     mock_mermaid_definition = """<pre class="mermaid">
#             graph TD
#             A[Client] -->|tcp_123| B
#             B(Load Balancer)
#             B -->|tcp_456| C[Server1]
#             B -->|tcp_456| D[Server2]
#     </pre>"""
#     # graph TD __start__["__start__"] travel_agent["travel_agent"] language_assistant["language_assistant"] visualizer["visualizer"] designer["designer"] bb6936485e364c8880a6132667c0f271["ChatPromptTemplate"] 153ea937f2b54bb88465d0751ab06cb3["ChatOpenAI"] bd70292b68f548dbab6ab5e330f0f140["JsonOutputFunctionsParser"] __end__["__end__"] bb6936485e364c8880a6132667c0f271 --> 153ea937f2b54bb88465d0751ab06cb3 153ea937f2b54bb88465d0751ab06cb3 --> bd70292b68f548dbab6ab5e330f0f140 __start__ --> bb6936485e364c8880a6132667c0f271 designer --> __end__ language_assistant --> bb6936485e364c8880a6132667c0f271 travel_agent --> bb6936485e364c8880a6132667c0f271 visualizer --> bb6936485e364c8880a6132667c0f271 bd70292b68f548dbab6ab5e330f0f140 --> travel_agent bd70292b68f548dbab6ab5e330f0f140 --> language_assistant bd70292b68f548dbab6ab5e330f0f140 --> visualizer bd70292b68f548dbab6ab5e330f0f140 -->|FINISH| designer

#     # Render the diagram with proper HTML structure
#     st.markdown(f"""
#         <pre class="mermaid">
#             {mock_mermaid_definition}
#         </pre>
#         <script type="module">
#             import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
#             mermaid.initialize({{ startOnLoad: true }});
#         </script>
#     """, unsafe_allow_html=True)
    
#     st.caption(chain_selection)

# def displayGraph(chain, chain_selection):
#     # Get the graph
#     graph = chain.get_graph(xray=True)
    
#     # Create Mermaid syntax with proper indentation
#     mermaid_lines = [
#         "            graph TD"
#     ]
    
#     # Add nodes with indentation and replace spaces with underscores
#     for node_id, node in graph.nodes.items():
#         node_id_processed = node.name.replace(" ", "_")
#         mermaid_lines.append(f'            {node_id_processed}["{node.name}"]')
    
#     # Add edges with indentation and replace spaces with underscores in node references
#     for edge in graph.edges:
#         source = edge.source.replace(" ", "_")
#         target = edge.target.replace(" ", "_")
#         if edge.conditional and edge.data:
#             mermaid_lines.append(f'            {source} -->|{edge.data}| {target}')
#         else:
#             mermaid_lines.append(f'            {source} --> {target}')
    
#     mermaid_definition = "\n".join(mermaid_lines)
    
#     # Create complete HTML with mermaid
#     # check visually on https://mermaid.live/
#     # comparison - https://swimm.io/learn/mermaid-js/mermaid-js-a-complete-guide
#     # repo - https://github.com/mermaid-js/mermaid
#     # plugin - https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid

#     html_content = f"""
#     <html>
#       <body>
#         <pre class="mermaid">
#             {mermaid_definition}
#         </pre>
        
#         <script type="module">
#           import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
#           mermaid.initialize({{ startOnLoad: true }});
#         </script>
        
#         <!--
#         <script type="module">
#             import mermaid from './mermaid.esm.mjs';
#             mermaid.initialize({{ startOnLoad: false, logLevel: 0 }});
#             await mermaid.run();
#         </script>
#         -->
#         <!--
#         <script src="mermaid.min.js"></script>
# 	    <script>mermaid.initialize({{startOnLoad:true}});</script>
#         -->
#       </body>
#     </html>
#     """
    
#     # Use components.v1.html to render
#     st.components.v1.html(html_content, height=600)
#     st.caption(chain_selection)



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

def render_chat_history_and_thoughts(chat_history, output=None):
    with st.container():
        # Render chat history
        for message in chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Render download link
        if chat_history:
            chat_history_str = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
            href = f'data:text/plain;charset=utf-8,{urllib.parse.quote(chat_history_str)}'
            st.markdown(f'<a href="{href}" download="chat_history.txt">Download Chat History</a>', unsafe_allow_html=True)
        
        # Render agent thoughts
        if output:
            with st.expander("Display Agent's Thoughts"):
                st.write(output)

def run_chatbot_graph(graph, input, config):
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    response_container = st.container()
    prompt_container = st.container()

    user_input = input["messages"][0].content
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    output = graph.invoke(input, config=config)
    
    # Extract AIMessage content from the string output
    if isinstance(output, dict):
        # response_value = str(next(iter(output.values())))
         response = output["messages"][-1].content
    else:
        # Find AIMessage content in the string
        ai_message_start = output.find("AIMessage(content='") + len("AIMessage(content='")
        ai_message_end = output.find("', response_metadata")
        response = output[ai_message_start:ai_message_end]
    
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    
    # Call the render method
    render_chat_history_and_thoughts(st.session_state.chat_history, output)


if __name__ == "__main__":
    main()