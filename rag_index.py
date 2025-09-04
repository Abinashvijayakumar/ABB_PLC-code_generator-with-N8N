import os
import shutil
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma

SOURCE_DOCUMENTS_PATH = "./rag_source_documents"
PERSISTENT_STORAGE_PATH = "./rag_db"

def build_index():
    """
    Builds the vector index from PDF documents.
    This is a one-time, offline process.
    """
    # 1. Check if source documents exist
    if not os.path.exists(SOURCE_DOCUMENTS_PATH) or not os.listdir(SOURCE_DOCUMENTS_PATH):
        print(f"❌ ERROR: No source documents found in '{SOURCE_DOCUMENTS_PATH}'. Please add your PDF manual.")
        return

    # 2. Delete old database if it exists
    if os.path.exists(PERSISTENT_STORAGE_PATH):
        print(f"🗑️ Deleting old database at: {PERSISTENT_STORAGE_PATH}")
        shutil.rmtree(PERSISTENT_STORAGE_PATH)

    # 3. Load and process documents
    print(f"📚 Loading documents from: {SOURCE_DOCUMENTS_PATH}...")
    loader = PyPDFDirectoryLoader(SOURCE_DOCUMENTS_PATH)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    print(f"   ...found {len(documents)} document(s), split into {len(docs)} chunks.")

    # 4. Create embeddings and the vector store
    print("🧠 Creating embeddings and building the vector index... (This may take a few minutes)")
    embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma.from_documents(
        docs, 
        embedding_model, 
        persist_directory=PERSISTENT_STORAGE_PATH
    )
    print("✅✅✅ DONE! New vector index built and saved successfully in 'rag_db' folder.")
    print("You may now commit the 'rag_db' folder to your repository.")

if __name__ == "__main__":
    build_index()