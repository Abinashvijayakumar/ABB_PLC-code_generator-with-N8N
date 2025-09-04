import os
import shutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
import uvicorn

# --- CONFIGURATION ---
SOURCE_DOCUMENTS_PATH = "./rag_kb" 
PERSISTENT_STORAGE_PATH = "./rag_db"
embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

app = FastAPI()

@app.get("/health")
def health_check():
    """A simple endpoint that Docker can use to check if the service is running."""
    return {"status": "ok"}

# ...(The rest of the RAG service code is the same as the final version I provided you)...
# Make sure to include the /rebuild-index and /query-kb endpoints.