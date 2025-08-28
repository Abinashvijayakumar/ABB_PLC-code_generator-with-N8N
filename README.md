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
