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
load_dotenv()
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key: raise ValueError("GOOGLE_API_KEY not found")
    genai.configure(api_key=api_key)
    print("✅ Google AI SDK configured successfully.")
except Exception as e:
    print(f"❌ Error configuring SDK: {e}"); exit()

# --- 2. PROMPT ENGINEERING (Definitive Version) ---
SYSTEM_PROMPT = """You are an expert-level PLC programming assistant...""" # (Your full v7.0 prompt)
SELF_CORRECTION_PROMPT = """You are a PLC Syntax and Compatibility Reviewer...""" # (Your full self-correction prompt)
USER_PROMPT_TEMPLATE = """Remember your core instructions... User Request: \"{{ USER_PROMPT_GOES_HERE }}\"""" # (Your full reinforced user prompt)

# --- 3. FASTAPI APP INITIALIZATION ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class Prompt(BaseModel): prompt: str

# --- 4. HELPER FUNCTIONS ---
def call_rag_service(prompt: str) -> list:
    rag_service_url = "http://rag_service:8001/query-kb"
    try:
        response = requests.post(rag_service_url, json={"prompt": prompt}, timeout=10)
        response.raise_for_status()
        return response.json().get("snippets", [])
    except requests.exceptions.RequestException as e:
        print(f"⚠️ WARNING: Could not connect to RAG service at {rag_service_url}: {e}. Proceeding without RAG.")
        return []

def generate_from_llm(user_prompt: str, original_user_input: str, is_correction=False) -> dict:
    # LUCCI'S FIX: This function is now more resilient to AI errors.
    try:
        system_instruction = SELF_CORRECTION_PROMPT if is_correction else SYSTEM_PROMPT
        model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=system_instruction)
        response = model.generate_content(user_prompt)
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        print(f"⚠️ Initial JSON parse failed. Raw output was not JSON. Error: {e}")
        # --- CHAT FALLBACK LOGIC ---
        chat_keywords = ["hi", "hello", "thanks", "thank you", "hey"]
        is_short_prompt = len(original_user_input.split()) <= 3
        is_greeting = any(keyword in original_user_input.lower() for keyword in chat_keywords)

        if is_short_prompt or is_greeting:
            print("...Identified as likely chat. Wrapping raw response in chat JSON.")
            return {"response_type": "chat", "message": response.text.strip()}
        else:
            print(f"❌ ERROR: Failed to parse JSON from a complex prompt.")
            raise HTTPException(status_code=500, detail=f"The AI returned a malformed response: {response.text}")
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"An unexpected error occurred with the AI model: {e}")

# --- 5. MAIN API ENDPOINT ---
@app.post("/generate")
def generate_and_verify_endpoint(prompt: Prompt):
    # This is the final version of the endpoint with RAG and self-correction
    # ...(Full code from previous definitive version)...
    rag_snippets = call_rag_service(prompt.prompt)
    #... etc.
    final_json = generate_from_llm(correction_user_prompt, original_user_input=prompt.prompt, is_correction=True)
    return {"response_type": "plc_code", "final_json": final_json}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)