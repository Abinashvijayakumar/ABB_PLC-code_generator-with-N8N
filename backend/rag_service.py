import os
import shutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# --- UPDATED IMPORTS ---
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
# ---
from langchain.text_splitter import RecursiveCharacterTextSplitter
import uvicorn

# --- CONFIGURATION ---
SOURCE_DOCUMENTS_PATH = "./rag_kb"
PERSISTENT_STORAGE_PATH = "./rag_db"

# This line now uses the updated class name, but the logic is the same.
# It will trigger the download from Hugging Face.
embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# The rest of your rag_service.py code remains the same...
app = FastAPI()


# --- LUCCI'S FIX: ADD THIS HEALTH CHECK ENDPOINT ---
@app.get("/health")
def health_check():
    """A simple endpoint that Docker can use to check if the service is running."""
    return {"status": "ok"}


def load_and_split_documents():
    if not os.path.exists(SOURCE_DOCUMENTS_PATH) or not os.listdir(SOURCE_DOCUMENTS_PATH):
        print(f"⚠ No documents found in {SOURCE_DOCUMENTS_PATH}. The knowledge base will be empty.")
        return []
    print(f"📚 Loading documents from: {SOURCE_DOCUMENTS_PATH}")
    loader = PyPDFDirectoryLoader(SOURCE_DOCUMENTS_PATH)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    print(f"   ...found {len(documents)} document(s), split into {len(docs)} chunks.")
    return docs

@app.post("/rebuild-index")
def rebuild_vector_database():
    try:
        if os.path.exists(PERSISTENT_STORAGE_PATH):
            print(f"🗑 Deleting old database at: {PERSISTENT_STORAGE_PATH}")
            shutil.rmtree(PERSISTENT_STORAGE_PATH)
        docs = load_and_split_documents()
        if not docs:
            return {"status": "success", "message": "Knowledge base is empty. No index was built."}
        print("🧠 Creating new vector index...")
        db = Chroma.from_documents(docs, embedding_model, persist_directory=PERSISTENT_STORAGE_PATH)
        print("✅ New vector index built and saved successfully.")
        return {"status": "success", "message": f"Index rebuilt with {len(docs)} document chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild index: {e}")

class Query(BaseModel):
    prompt: str

@app.post("/query-kb")
def query_knowledge_base(query: Query):
    if not os.path.exists(PERSISTENT_STORAGE_PATH):
        return {"snippets": []}
    try:
        db = Chroma(persist_directory=PERSISTENT_STORAGE_PATH, embedding_function=embedding_model)
        retriever = db.as_retriever(search_kwargs={'k': 3})
        relevant_docs = retriever.get_relevant_documents(query.prompt)
        snippets = [doc.page_content for doc in relevant_docs]
        return {"snippets": snippets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query knowledge base: {e}")

@app.on_event("startup")
async def startup_event():
    if not os.path.exists(PERSISTENT_STORAGE_PATH):
        print("No existing database found. Building initial index...")
        rebuild_vector_database()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)