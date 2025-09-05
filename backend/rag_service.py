import os
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

class Query(BaseModel):
    prompt: str


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
    