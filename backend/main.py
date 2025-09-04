import os
import json
import requests
import uvicorn
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# --- 1. SETUP AND CONFIGURATION ---
# (This section remains the same)
load_dotenv()
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key: raise ValueError("GOOGLE_API_KEY not found")
    genai.configure(api_key=api_key)
    print("✅ Google AI SDK configured successfully.")
except Exception as e:
    print(f"❌ Error configuring SDK: {e}"); exit()

# --- 2. PROMPT ENGINEERING (Definitive Version) ---
# (All your prompts remain the same)
SYSTEM_PROMPT = """You are an expert PLC programmer and a helpful AI assistant..."""
SELF_CORRECTION_PROMPT = """You are a PLC Syntax and Compatibility Reviewer..."""
USER_PROMPT_TEMPLATE = "User Request: \"{{ USER_PROMPT_GOES_HERE }}\""

# --- 3. FASTAPI APP INITIALIZATION ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class Prompt(BaseModel): prompt: str

# --- 4. HELPER FUNCTIONS ---
def call_rag_service(prompt: str) -> list:
    # LUCCI'S FIX: The URL is now the Docker service name, not localhost.
    # This allows the containers to communicate with each other.
    rag_service_url = "http://rag_service:8001/query-kb"
    try:
        response = requests.post(rag_service_url, json={"prompt": prompt}, timeout=5)
        response.raise_for_status()
        return response.json().get("snippets", [])
    except requests.exceptions.RequestException as e:
        # This is the error you were seeing in the container logs.
        print(f"⚠️ CRITICAL WARNING: Could not connect to RAG service at {rag_service_url}: {e}. Proceeding without RAG.")
        return []

def generate_from_llm(user_prompt: str, is_correction=False) -> dict:
    # (This function remains the same)
    try:
        current_model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SELF_CORRECTION_PROMPT if is_correction else SYSTEM_PROMPT)
        response = current_model.generate_content(user_prompt)
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except Exception as e:
        raw_output = response.text if 'response' in locals() else "No response from model."
        print(f"❌ ERROR: Failed to parse JSON from LLM response: {e}\nRaw AI Output:\n---\n{raw_output}\n---")
        raise HTTPException(status_code=500, detail="The AI returned a malformed response.")

# --- 5. MAIN API ENDPOINT ---
# (This entire endpoint remains the same, as it already calls the helper function)
@app.post("/generate")
def generate_and_verify_endpoint(prompt: Prompt):
    print(f"Received prompt: {prompt.prompt}")

    print("A. Calling RAG service for relevant examples...")
    rag_snippets = call_rag_service(prompt.prompt)
    rag_context = "\n\n".join(rag_snippets)
    user_prompt = USER_PROMPT_TEMPLATE.replace("{{ USER_PROMPT_GOES_HERE }}", prompt.prompt)
    if rag_context:
        print("   ...RAG context found. Injecting into prompt.")
        user_prompt += f"\n\nHere is some relevant context from our knowledge base to help you:\n---\n{rag_context}\n---"
    
    print("1. Calling LLM for initial generation...")
    generated_json = generate_from_llm(user_prompt)
    
    if generated_json.get("response_type") == "chat":
        print("✅ Intent is 'chat'. Returning response.")
        return generated_json

    if generated_json.get("response_type") != "plc_code":
        raise HTTPException(status_code=500, detail="AI returned an unknown response type.")

    print("✅ Intent is 'generate_code'. Proceeding to self-correction review.")
    time.sleep(1)

    print("2. Sending code back to LLM for self-correction review...")
    correction_user_prompt = f"Please review and correct the following generated JSON:\n\n{json.dumps(generated_json)}"
    final_json = generate_from_llm(correction_user_prompt, is_correction=True)

    print("3. Self-correction review complete.")
    return {"response_type": "plc_code", "final_json": final_json}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

