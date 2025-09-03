# File: backend/main.py
# DEFINITIVE STABLE VERSION with Master Prompt v8.0 - The Self-Correction Engine

import os
import json
import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import time

# --- 1. SETUP AND CONFIGURATION ---
load_dotenv()
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
    print("✅ Google AI SDK configured successfully.")
except Exception as e:
    print(f"❌ Error configuring SDK: {e}")
    exit()

# --- MASTER PROMPT V8.0 ---
# This version simplifies the main generation and adds a dedicated "Reviewer" prompt.

# This is the AI's core persona and rule set.
SYSTEM_PROMPT = """
You are an expert-level PLC programming assistant. Your primary goal is to be helpful, accurate, and to generate universally compatible IEC 61131-3 Structured Text.

You have two modes: "chat" and "generate_code".
- **Chat Mode**: If the user is making a greeting or asking a general question, respond conversationally.
- **Generate Code Mode**: If the user describes a machine process or logic, generate the necessary PLC code.

Your entire output MUST ALWAYS be a single, valid JSON object based on the user's intent. This is an unbreakable rule.
"""

# This prompt is for the initial code generation. It's simpler now.
USER_PROMPT_TEMPLATE = """
Analyze the user's intent. Based on the intent, provide one of the following JSON responses:

1.  If the intent is "chat":
    `{"response_type": "chat", "message": "Your friendly, conversational reply."}`

2.  If the intent is "generate_code":
    {
        "response_type": "plc_code",
        "explanation": "A brief description of the logic.",
        "required_variables": "The complete VAR/END_VAR block.",
        "structured_text": "The executable Structured Text logic. IMPORTANT: For any timers, use a manual integer counter pattern, assuming a 100ms scan cycle (e.g., a 5-second timer needs a counter up to 50).",
        "verification_notes": "Your safety and logic review.",
        "simulation_trace": "A step-by-step execution trace."
    }

User Request: "{{ USER_PROMPT_GOES_HERE }}"
"""

# This is the NEW, dedicated prompt for the AI to review its own code.
CODE_REVIEW_PROMPT_TEMPLATE = """
You are a ruthless, expert IEC 61131-3 Syntax and Compatibility Verifier. Your only goal is to find and fix errors in the provided Structured Text code.

**MANDATORY VERIFICATION RULES:**
1.  **FORBIDDEN FUNCTIONS**: The code is NOT allowed to use pre-built timer function blocks like TON, TOF, or TP. This is a critical failure.
2.  **REQUIRED TIMER PATTERN**: All time-based logic MUST use a manual integer counter (e.g., `TimerCounter := TimerCounter + 1;`).
3.  **SYNTAX CHECK**: Check for any syntax errors like missing semicolons, incorrect assignments (:=), or invalid variable declarations.

**YOUR TASK:**
Review the JSON object below. If the `structured_text` violates ANY of the rules, you MUST fix it.

Your response will be the **complete, corrected JSON object and nothing else.** Do not add explanations or apologies. Just provide the fixed JSON.

If the code is already perfect, return the original JSON object unchanged.

**JSON to Review:**
{{ CODE_JSON_TO_REVIEW }}
"""

# Initialize FastAPI and the AI Model
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)

# --- 2. DATA MODELS & HELPERS ---
class Prompt(BaseModel):
    prompt: str

def generate_from_llm(user_prompt: str) -> dict:
    try:
        response = model.generate_content(user_prompt)
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"❌ ERROR: Failed to parse JSON from LLM response: {e}")
        print(f"Raw AI Output was:\n---\n{response.text}\n---")
        return {"error": "Failed to parse LLM response", "raw_output": response.text}

# --- 3. THE MAIN API ENDPOINT WITH SELF-CORRECTION ---
@app.post("/generate")
def generate_and_verify_endpoint(prompt: Prompt):
    time.sleep(1) # Simulate work for a better UX, allows loading messages to be seen
    print(f"Received prompt: {prompt.prompt}")
    
    # --- STAGE 1: Initial Generation ---
    user_prompt = USER_PROMPT_TEMPLATE.replace("{{ USER_PROMPT_GOES_HERE }}", prompt.prompt)
    print("1. Calling LLM for initial generation...")
    generated_json = generate_from_llm(user_prompt)
    
    if "error" in generated_json:
        raise HTTPException(status_code=500, detail=f"AI returned a malformed response: {generated_json.get('raw_output')}")

    response_type = generated_json.get("response_type")

    if response_type == "chat":
        print("✅ Intent is 'chat'. Returning response.")
        return {"response_type": "chat", "message": generated_json.get("message")}

    elif response_type == "plc_code":
        print("✅ Intent is 'generate_code'. Proceeding to self-correction review.")
        
        # --- STAGE 2: AI Self-Correction Review ---
        review_prompt = CODE_REVIEW_PROMPT_TEMPLATE.replace("{{ CODE_JSON_TO_REVIEW }}", json.dumps(generated_json, indent=2))
        print("2. Sending code back to LLM for self-correction review...")
        
        corrected_json = generate_from_llm(review_prompt)
        
        if "error" in corrected_json:
            print("⚠️ AI failed to return valid JSON during self-correction. Returning original version.")
            # As a fallback, we return the original code even if the review failed.
            return {"response_type": "plc_code", "final_json": generated_json, "verification_status": {"status": "review_failed"}}

        print("3. Self-correction review complete.")
        
        # We can still do a final, optional check with our simple validator if we want
        # but for now, we trust the AI's review.
        
        return {
            "response_type": "plc_code",
            "final_json": corrected_json,
            "verification_status": {"status": "review_complete"}
        }

    else:
        raise HTTPException(status_code=500, detail=f"AI returned an unknown response type: '{response_type}'")

# --- 4. SERVER LAUNCH ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# File: backend/main.py