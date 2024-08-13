from langchain.tools import tool
from pydantic import BaseModel, Field
# from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings
# from langchain.vectorstores import Chroma
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
import logging
import os

class RAGInput(BaseModel):
    query: str = Field(description="The question to be answered using the RAG system.")
    pdf_path: str = Field(description="Path to the PDF file to be used as the knowledge base.")

@tool("rag_query", args_schema=RAGInput)
def rag_query(query: str, pdf_path: str) -> str:
    """Query a PDF document using RAG (Retrieval-Augmented Generation)."""
    
    # Load the PDF
    loader = PyPDFLoader(pdf_path)
    pages = loader.load_and_split()

    # Split the text into chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(pages)

    # Create embeddings and load them into Chroma
    embeddings = OpenAIEmbeddings()
    # db = Chroma.from_documents(texts, embeddings)
    db = FAISS.from_documents(texts, embeddings)

    # Perform similarity search
    docs = db.similarity_search(query)

    # Format the response
    response = f"Based on the PDF content, here's the relevant information:\n\n"
    for doc in docs:
        response += f"{doc.page_content}\n\n"

    return response

if __name__ == "__main__":
    #Enable logging
    logging.basicConfig(level=logging.INFO)
    pdf_path = "D:\code\langgraph_agents\output\Glasgow-1day.pdf"
    query = "What is the main topic of this document?"
    print(rag_query.run({"query": query, "pdf_path": pdf_path}))
