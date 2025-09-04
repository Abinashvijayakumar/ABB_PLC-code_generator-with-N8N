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
    if not api_key: raise ValueError("GOOGLE_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
    print("✅ Google AI SDK configured successfully.")
except Exception as e:
    print(f"❌ Error configuring SDK: {e}"); exit()

# --- 2. PROMPT ENGINEERING (Definitive v9.0) ---
SYSTEM_PROMPT = """You are an expert-level PLC programming assistant. You are a precise, logical, and helpful AI that follows instructions perfectly.

<SYSTEM_RULES>
1.  **Analyze Intent**: Your first task is to determine if the user's request is for a "chat" or to "generate_code".
2.  **Strict JSON Output**: Your entire response MUST be a single, valid JSON object. Do not include any conversational text, markdown, apologies, or explanations outside of the JSON structure. This is an unbreakable rule.
3.  **Universal Code Mandate**: All generated PLC code must be universally compatible IEC 61131-3 Structured Text.
    - **FORBIDDEN FUNCTIONS**: You are strictly forbidden from using any pre-built timer function blocks like TON, TOF, or TP.
    - **REQUIRED TIMER PATTERN**: For ALL time-based logic, you MUST ONLY use a manual integer counter pattern. Assume a 100ms scan cycle (5 seconds = 50 cycles).
</SYSTEM_RULES>

<OUTPUT_FORMATS>
-   **For "chat" intent**: Respond with `{"response_type": "chat", "message": "Your conversational reply."}`
-   **For "generate_code" intent**: Respond with this exact 6-key JSON structure:
    {
        "response_type": "plc_code",
        "explanation": "A brief description of the logic.",
        "required_variables": "The complete VAR/END_VAR block.",
        "structured_text": "The executable Structured Text logic.",
        "verification_notes": "Your safety and logic review.",
        "simulation_trace": "A step-by-step execution trace."
    }
</OUTPUT_FORMATS>
"""

SELF_CORRECTION_PROMPT = """You are a PLC Syntax and Compatibility Reviewer. Review the provided JSON. Check the `structured_text` for any syntax errors or violations of the Universal Compatibility Guide (especially the manual timer rule). Your only output must be the complete, corrected 6-key JSON object."""

USER_PROMPT_TEMPLATE = "<USER_REQUEST>{{ USER_PROMPT_GOES_HERE }}</USER_REQUEST>"

# --- 3. FASTAPI APP INITIALIZATION ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class Prompt(BaseModel): prompt: str

# --- 4. HELPER FUNCTIONS ---
def call_rag_service(prompt: str) -> list:
    rag_service_url = "http://localhost:8001/query-kb"
    try:
        response = requests.post(rag_service_url, json={"prompt": prompt}, timeout=5)
        response.raise_for_status()
        return response.json().get("snippets", [])
    except requests.exceptions.RequestException as e:
        print(f"⚠️ WARNING: Could not connect to RAG service: {e}. Proceeding without RAG.")
        return []

def generate_from_llm(user_prompt: str, is_correction=False) -> dict:
    try:
        system_instruction = SELF_CORRECTION_PROMPT if is_correction else SYSTEM_PROMPT
        model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=system_instruction)
        response = model.generate_content(user_prompt)
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except Exception as e:
        raw_output = response.text if 'response' in locals() else "No response from model."
        print(f"❌ ERROR: Failed to parse JSON from LLM response: {e}\nRaw AI Output:\n---\n{raw_output}\n---")
        raise HTTPException(status_code=500, detail="The AI returned a malformed response.")

# --- 5. MAIN API ENDPOINT ---
@app.post("/generate")
def generate_and_verify_endpoint(prompt: Prompt):
    print(f"Received prompt: {prompt.prompt}")
    rag_snippets = call_rag_service(prompt.prompt)
    rag_context = "\n\n".join(rag_snippets)
    user_prompt = USER_PROMPT_TEMPLATE.replace("{{ USER_PROMPT_GOES_HERE }}", prompt.prompt)
    if rag_context:
        user_prompt += f"\n\n<CONTEXT_FROM_KNOWLEDGE_BASE>{rag_context}</CONTEXT_FROM_KNOWLEDGE_BASE>"
    
    print("1. Calling LLM for initial generation...")
    generated_json = generate_from_llm(user_prompt)
    
    if generated_json.get("response_type") == "chat":
        return generated_json

    if generated_json.get("response_type") != "plc_code":
        raise HTTPException(status_code=500, detail="AI returned an unknown response type.")

    print("2. Proceeding to AI self-correction review...")
    time.sleep(1)
    correction_user_prompt = f"<JSON_TO_REVIEW>{json.dumps(generated_json)}</JSON_TO_REVIEW>"
    final_json = generate_from_llm(correction_user_prompt, is_correction=True)

    print("3. Self-correction review complete.")
    return {"response_type": "plc_code", "final_json": final_json}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)