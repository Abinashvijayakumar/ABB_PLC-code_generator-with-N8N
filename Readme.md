Clone the Repo: git clone <your-repo-url>

Switch to the Develop Branch: git checkout develop

Create the Project Structure: Collectively create the initial folders and blank files so everyone is working from the same blueprint.

abb-plc-ai-copilot/
|-- backend/
|   |-- scripts/
|   |   |-- verify_st.py
|   |-- main.py                 # For FastAPI later
|   |-- verification_service.py # For Phase 1
|   |-- rag_service.py          # For Phase 1
|-- frontend/
|   |-- index.html
|   |-- style.css
|   |-- app.js
|-- rag_kb/
|   |-- example1.md
|-- .gitignore
|-- requirements.txt
|-- README.md
Setup Python Environment:

Run python -m venv venv in the root directory.

Activate it: source venv/bin/activate (or .\venv\Scripts\activate on Windows).

Populate requirements.txt with the essentials for now. Copy-paste this in:

# Core FastAPI for services
fastapi
uvicorn[standard]

# LLM SDK
google-generativeai
python-dotenv

# RAG / Vector Store
chromadb
langchain
sentence-transformers

# For making requests between services
requests
Install them: pip install -r requirements.txt

Once this is done, you have a clean, professional workspace ready for tomorrow. Push the initial file structure to the develop branch.