import os
<<<<<<< HEAD
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import uvicorn

PERSISTENT_STORAGE_PATH = "./rag_db"
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
app = FastAPI()

# Load the database on startup
if not os.path.exists(PERSISTENT_STORAGE_PATH):
    raise RuntimeError("❌ RAG database not found! Please run 'build_rag_index.py' first.")

print("🧠 Loading existing RAG database...")
db = Chroma(persist_directory=PERSISTENT_STORAGE_PATH, embedding_function=embedding_model)
retriever = db.as_retriever(search_kwargs={'k': 3})
print("✅ RAG database loaded successfully.")
=======
import shutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
import uvicorn

# --- CONFIGURATION ---
# This is the folder on your computer where you will store your PDFs.
# It will be mapped into the Docker container.
SOURCE_DOCUMENTS_PATH = "./rag_kb" 
# This is the folder inside the container where the vector database will be stored.
PERSISTENT_STORAGE_PATH = "./rag_db"

# Initialize the embedding model
embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# --- FASTAPI APP INITIALIZATION ---
app = FastAPI()

# --- HELPER FUNCTIONS ---

def load_and_split_documents():
    """Loads PDFs from the source folder and splits them into chunks."""
    if not os.path.exists(SOURCE_DOCUMENTS_PATH) or not os.listdir(SOURCE_DOCUMENTS_PATH):
        print(f"⚠️ No documents found in {SOURCE_DOCUMENTS_PATH}. The knowledge base will be empty.")
        return []
        
    print(f"📚 Loading documents from: {SOURCE_DOCUMENTS_PATH}")
    loader = PyPDFDirectoryLoader(SOURCE_DOCUMENTS_PATH)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    print(f"   ...found {len(documents)} document(s), split into {len(docs)} chunks.")
    return docs

# --- API ENDPOINTS ---

@app.post("/rebuild-index")
def rebuild_vector_database():
    """
    Deletes the old database, re-scans the source documents folder,
    and builds a new vector index from scratch.
    """
    try:
        # 1. Delete the old database if it exists
        if os.path.exists(PERSISTENT_STORAGE_PATH):
            print(f"🗑️ Deleting old database at: {PERSISTENT_STORAGE_PATH}")
            shutil.rmtree(PERSISTENT_STORAGE_PATH)

        # 2. Load and process new documents
        docs = load_and_split_documents()
        if not docs:
            return {"status": "success", "message": "Knowledge base is empty. No index was built."}

        # 3. Create a new vector store
        print("🧠 Creating new vector index...")
        db = Chroma.from_documents(
            docs, 
            embedding_model, 
            persist_directory=PERSISTENT_STORAGE_PATH
        )
        print("✅ New vector index built and saved successfully.")
        
        return {"status": "success", "message": f"Index rebuilt with {len(docs)} document chunks."}

    except Exception as e:
        print(f"❌ CRITICAL ERROR during index rebuild: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rebuild index: {e}")

>>>>>>> d9fe18e (rag file)

class Query(BaseModel):
    prompt: str

<<<<<<< HEAD

@app.post("/query-kb")
def query_knowledge_base(query: Query):
    try:
        relevant_docs = retriever.get_relevant_documents(query.prompt)
        snippets = [doc.page_content for doc in relevant_docs]
        return {"snippets": snippets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query knowledge base: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
    
=======
@app.post("/query-kb")
def query_knowledge_base(query: Query):
    """
    Searches the vector database for documents relevant to the user's prompt.
    """
    if not os.path.exists(PERSISTENT_STORAGE_PATH):
        return {"snippets": []} # Return empty if no database exists
        
    try:
        # Load the existing vector store
        db = Chroma(
            persist_directory=PERSISTENT_STORAGE_PATH, 
            embedding_function=embedding_model
        )
        
        # Search for relevant documents
        retriever = db.as_retriever(search_kwargs={'k': 3}) # Retrieve top 3 chunks
        relevant_docs = retriever.get_relevant_documents(query.prompt)
        
        # Format the results
        snippets = [doc.page_content for doc in relevant_docs]
        return {"snippets": snippets}

    except Exception as e:
        print(f"❌ ERROR during query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to query knowledge base: {e}")


# --- INITIALIZATION LOGIC ---

@app.on_event("startup")
async def startup_event():
    """
    This code runs once when the server starts up.
    It checks if a database exists. If not, it builds one automatically.
    """
    if not os.path.exists(PERSISTENT_STORAGE_PATH):
        print("No existing database found. Building initial index...")
        rebuild_vector_database()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

### **Step 2: Update the `docker-compose.yml` to Use Volumes**

Now we tell Docker about our new data-centric approach.

**Action:** Replace your `docker-compose.yml` with this updated version. I have added the `volumes` section.

```yaml
# File: docker-compose.yml
# This file defines and runs our entire multi-container application.

version: '3.8'

services:
  # The Main Orchestrator Service (main.py)
  orchestrator:
    build:
      context: .
      dockerfile: Dockerfile
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app/backend # Mount local code for live reloading
    env_file:
      - .env

  # The RAG Service (rag_service.py)
  rag_service:
    build:
      context: .
      dockerfile: Dockerfile
    command: uvicorn backend.rag_service:app --host 0.0.0.0 --port 8001
    volumes:
      # This is the magic:
      # Mounts the local rag_kb folder into the container
      - ./rag_kb:/app/rag_kb
      # Mounts a local folder to store the persistent database
      - ./rag_db:/app/rag_db

  # The Frontend Service (Nginx)
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "8080:80" # We will access the UI on http://localhost:8080
    depends_on:
      - orchestrator # Ensures the backend starts before the frontend

```

---

### **Step 3: The Final Workflow**

Your project is now fully professionalized.

1.  **Place Your PDFs:** Create a folder named `rag_kb` in your project's root directory. Place the PDF books you want to use inside this folder.
2.  **Build and Run Everything:** Launch your entire application with a single command:
    ```bash
    docker-compose up --build
    ```
    * On the very first launch, the RAG service will detect that there is no database. It will automatically read the PDFs from `rag_kb`, process them, and build the vector store inside a new `rag_db` folder.
3.  **Use the Application:** Your main application at `http://localhost:8080` will now be supercharged with knowledge from your PDF books.
4.  **Update Your Knowledge:**
    * Stop the containers (`Ctrl+C`).
    * Add, remove, or change the PDF files in your local `rag_kb` folder.
    * Restart the containers: `docker-compose up`.
    * The RAG service will start, see the existing `rag_db`, and use it. To force it to re-read the new PDFs, you will now send a `POST` request to the re-indexing endpoint (e.g., using PowerShell or a simple script):
        ```powershell
        Invoke-RestMethod -Uri "http://localhost:8001/rebuild-index" -Method POST
        
>>>>>>> d9fe18e (rag file)
