PLC Co-pilot: AI-Powered Industrial Automation Assistant
An advanced AI assistant designed to accelerate industrial automation by generating, verifying, and explaining IEC 61131-3 Structured Text code. This tool acts as an intelligent partner for PLC programmers and automation engineers.

## 🌐 Try the Demo
**Live Demo:** [https://Abinashvijayakumar.github.io/ABB_PLC-code_generator-with-N8N](https://Abinashvijayakumar.github.io/ABB_PLC-code_generator-with-N8N)

Experience the PLC Co-pilot interface with sample responses that demonstrate the complete workflow from natural language input to generated PLC code. The demo showcases realistic examples including start/stop motor controls, timer implementations, and more.

🚀 Key Features
Advanced AI Code Generation: Leverages Google's Gemini models to translate natural language descriptions into high-quality, universally compatible Structured Text.

Retrieval-Augmented Generation (RAG): The AI's knowledge is augmented with information from your private technical manuals and PDFs, ensuring context-aware and factually grounded answers.

AI Self-Correction Loop: A unique two-step verification process where the AI reviews and corrects its own generated code, dramatically improving reliability and adherence to standards.

Structured, Multi-Part Output: Provides a complete solution package including code, variable declarations, a professional explanation, verification notes, and a simulation trace.

Professional Microservices Architecture: Built with a decoupled backend featuring a main orchestrator and a specialized rag_service for scalability and robustness.

Fully Containerized: The entire application is containerized with Docker, ensuring a consistent and easy-to-manage development and deployment environment.

🏛️ Architecture Overview
The PLC Co-pilot is built on a modern, multi-service architecture designed for scalability and maintainability.

(It is highly recommended to create a simple diagram and link it here)

Frontend: A static, single-page application built with HTML, CSS, and JavaScript that provides the user interface.

Orchestrator Service: The central "brain" of the application. A FastAPI server that handles user prompts, coordinates with the RAG service, and manages the multi-step LLM workflow.

RAG Service: A specialized FastAPI microservice that provides a queryable knowledge base, running a Chroma vector database to find relevant context from source documents.

🛠️ Tech Stack
Component	Technologies & Frameworks
Frontend	HTML5, CSS3, JavaScript
Backend	Python 3.11+, FastAPI, Uvicorn
AI & Machine Learning	Google Generative AI (Gemini), LangChain, ChromaDB (Vector Store), Sentence Transformers (Embeddings)
Containerization	Docker, Docker Compose
CI/CD & Deployment	GitHub Actions, Google Cloud Run / Render

Export to Sheets
⚙️ Getting Started: Local Setup
Follow these steps to set up and run the project on your local machine.

Prerequisites
Git

Docker and Docker Compose

Python 3.11+

Installation & Launch
Clone the repository:

Bash

git clone https://github.com/your-username/your-repo.git
cd your-repo
Create an environment file:
Create a file named .env in the root of the project and add your Google API key:

Code snippet

GOOGLE_API_KEY=your_actual_google_api_key_here
Add Knowledge Base Documents:
Place your PLC technical manuals (PDF files) inside the ./rag_source_documents directory.

Build the RAG Index:
This is a one-time setup step to create the vector database.

Bash

# It's recommended to use a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python rag_index.py
This will create a rag_db folder containing the knowledge base.

Build and Run the Application:
This single command will build all the Docker images and start the services.

Bash

docker-compose up --build
Access the Application:
Once the containers are running, open your web browser and navigate to:
http://localhost:8080

🚀 Usage
Open the web interface.

Type a natural language description of the PLC logic you need in the chat input.

Press "Send" or hit Enter.

The AI will generate the full solution in the output panel, organized into tabs for Structured Text, Variables, and Simulation.

You can edit the generated code and variables directly in the text areas.

Use the download buttons to save the generated code and variables as separate files.

📄 License
This project is licensed under the MIT License. See the LICENSE file for details.
