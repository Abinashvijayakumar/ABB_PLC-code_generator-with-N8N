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
    if not api_key: raise ValueError("GOOGLE_API_KEY not found in .env file or environment variables.")
    genai.configure(api_key=api_key)
    print("✅ Google AI SDK configured successfully.")
except Exception as e:
    print(f"❌ Error configuring SDK: {e}"); exit()

# --- 2. PROMPT ENGINEERING (Definitive Version) ---
SYSTEM_PROMPT = """You are an expert PLC programmer and a helpful AI assistant. You have two primary functions based on the user's intent: 'chat' or 'generate_code'.

**RULES:**
1.  **Intent Analysis:** First, determine the user's intent. If they are asking a question, greeting you, or not describing logic, the intent is 'chat'. If they describe a machine process or logic, the intent is 'generate_code'.
2.  **JSON ONLY:** Your entire response MUST be a single, valid JSON object. Do NOT use markdown or any text outside the JSON structure.

**RESPONSE FORMATS:**
-   **If intent is 'chat':** Respond with `{"response_type": "chat", "message": "Your conversational reply."}`
-   **If intent is 'generate_code':** Respond with the full 6-key JSON object: `{"response_type": "plc_code", "explanation": "...", "required_variables": "...", "structured_text": "...", "verification_notes": "...", "simulation_trace": "..."}`
-   **Code Generation Rules:**
    -   Generate simple, universally compatible IEC 61131-3 Structured Text.
    -   **DO NOT use vendor-specific function blocks like `TON`, `TOF`, or `CTU`**. You MUST create timers and counters manually using integer variables and checking the system clock or scan cycle time. This is a strict requirement for the target compiler."""

SELF_CORRECTION_PROMPT = """You are a PLC Syntax and Compatibility Reviewer. The user has provided PLC code that needs to be reviewed and corrected.

**YOUR TASK:**
1.  Analyze the provided `structured_text`.
2.  Check for any syntax errors, undeclared variables, or logical issues.
3.  **Strictly enforce the rule: DO NOT use vendor-specific function blocks like `TON` or `TOF`. All timers must be implemented manually.**
4.  Rewrite the code to be simple, correct, and universally compatible.
5.  Return the complete and corrected 6-key JSON object (`{"response_type": "plc_code", ...}`). Your entire output must be only the JSON object."""

USER_PROMPT_TEMPLATE = "User Request: \"{{ USER_PROMPT_GOES_HERE }}\""

# --- 3. FASTAPI APP INITIALIZATION ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)

class Prompt(BaseModel): prompt: str

# --- 4. HELPER FUNCTIONS ---
def call_rag_service(prompt: str) -> list:
    rag_service_url = "http://rag_service:8001/query-kb"
    try:
        response = requests.post(rag_service_url, json={"prompt": prompt}, timeout=5)
        response.raise_for_status()
        return response.json().get("snippets", [])
    except requests.exceptions.RequestException as e:
        print(f"⚠️ WARNING: Could not connect to RAG service at {rag_service_url}: {e}. Proceeding without RAG.")
        return []

def generate_from_llm(user_prompt: str, is_correction=False) -> dict:
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

