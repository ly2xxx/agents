from langchain.tools import tool
from pydantic import BaseModel, Field
# from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings
# from langchain.vectorstores import Chroma
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader
import logging

class RAGInput(BaseModel):
    query: str = Field(description="The question to be answered using the RAG system.")
    file_path: str = Field(description="Path to the file to be used as the knowledge base.")

@tool("rag_query", args_schema=RAGInput)
def rag_query(query: str, file_path: str) -> str:
    """Query a PDF or Markdown document using RAG (Retrieval-Augmented Generation)."""
    
    # Determine file type and load accordingly
    if file_path.lower().endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()
    elif file_path.lower().endswith('.md') or file_path.lower().endswith('.txt'):
        loader = TextLoader(file_path)
        pages = loader.load()
    else:
        raise ValueError("Unsupported file type. Please provide a PDF or Markdown txt file.")

    # Rest of the function remains the same
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(pages)

    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(texts, embeddings)

    docs = db.similarity_search(query)

    response = f"Based on the document content, here's the relevant information:\n\n"
    for doc in docs:
        response += f"{doc.page_content}\n\n"

    return response

if __name__ == "__main__":
    #Enable logging
    logging.basicConfig(level=logging.INFO)
    
    # Example with PDF
    pdf_path = "D:\code\langgraph_agents\output\Glasgow-1day.pdf"
    pdf_query = "What is the main topic of this document?"
    print(rag_query.run({"query": pdf_query, "file_path": pdf_path}))

    # Example with Markdown
    md_path = "D:\code\langgraph_agents\output\DDDvsTDD.md"
    md_query = "Summarize the content of this Markdown file."
    print(rag_query.run({"query": md_query, "file_path": md_path}))
