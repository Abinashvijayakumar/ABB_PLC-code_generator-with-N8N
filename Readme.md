# Install Core Tools:
Git: Version control is non-negotiable.
VS Code: Your primary Integrated Development Environment (IDE). Install the official Python, Docker, and GitLens extensions.
Python: Install version 3.10+. Ensure it's added to your system's PATH.
Docker Desktop: Essential for containerization, a "Must-Have" requirement.
n8n Desktop App: For local workflow development and testing.

## Team Collaboration & Repository Setup (Lead Architect)
Create GitHub Repository:
Initialize it with a Python 
.gitignore file, a README.md, and an empty requirements.txt.
Create the primary branches: 
main and develop.
Set a branch protection rule on 
main to require at least one pull request review before merging. This prevents accidental mistakes. All work will be done on feature branches and merged into
develop first.

### File Structure Setup (Lead Architect)
This structure is based on professional best practices and the provided documents. The Lead Architect will create this initial folder structure and push it to the develop branch.

/abb-plc-ai-generator
|
|-- /.github/           # For GitHub Actions (CI/CD later)
|-- /backend/
|   |-- /scripts/
|   |   |-- verify_st.py        # Python script for MATIEC verification [cite: 199]
|   |   |-- review_logic.py     # Python script for LLM self-correction
|   |   |-- generate_ld.py      # Python script for Ladder Logic generation [cite: 200]
|   |-- /rag_kb/              # Knowledge base for RAG [cite: 202, 223]
|   |   |-- start_stop_circuit.md
|   |   |-- ...
|
|-- /frontend/
|   |-- app.py                # Main Streamlit application file [cite: 224]
|
|-- /docs/                  # For presentation and project documents [cite: 207]
|-- .gitignore
|-- Dockerfile              # To containerize the entire application [cite: 101, 248]
|-- docker-compose.yml      # To manage multi-container setups [cite: 213]
|-- README.md               # Project documentation [cite: 136, 253]
|-- requirements.txt        # Python dependencies [cite: 56, 203]

#### Cloud Services & API Keys (Lead Architect)
Obtain API Keys:
Create an account on the 
Google AI Platform and generate an API key for the Gemini models. This will be our primary choice.
Create a backup account on 
OpenAI.
Secure Key Management:
Use a password manager or a secure method to share keys with the team. 

##### **Step 3: The Final Workflow**

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
        

######  **Step 2: Update the `docker-compose.yml` to Use Volumes**

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

