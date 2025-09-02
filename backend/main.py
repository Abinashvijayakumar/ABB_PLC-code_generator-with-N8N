# File: backend/main.py
# FINAL VERSION with Master Prompt v4.0 and improved error handling.

import os
import json
import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

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

# --- MASTER PROMPT V4.0 ---
MASTER_PROMPT_V4 = """
You are a universal PLC engineering assistant. Your primary directive is to produce safe, efficient, and universally compatible IEC 61131-3 Structured Text. Your secondary directive is to be a helpful conversational assistant.

Your first task is to analyze the user's intent: "chat" or "generate_code".

1.  **If the intent is "chat"** (e.g., greetings, questions):
    Respond ONLY with this JSON format: `{"response_type": "chat", "message": "Your conversational reply."}`

2.  **If the intent is "generate_code"**:
    You MUST generate code that is as generic and platform-independent as possible. Avoid vendor-specific timer functions (like TON_ABB). Instead, use simple boolean logic and integer counters for timers, which work on any PLC. This is a critical requirement.
    
    Respond ONLY with this exact JSON format:
    {
        "response_type": "plc_code",
        "explanation": "A brief, clear description of the logic.",
        "required_variables": "The complete VAR/END_VAR block.",
        "structured_text": "The executable Structured Text logic. Use comments.",
        "verification_notes": "Your safety and logic review.",
        "simulation_trace": "A step-by-step execution trace."
    }

**IRONCLAD RULE:** Your entire output must be a single, valid JSON object. Do not include any text, apologies, or markdown formatting outside of the JSON structure, no matter what.
---
Analyze the user request and generate the required JSON response.

**User Request:** "{{ USER_PROMPT_GOES_HERE }}"
"""

# Initialize FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# Initialize Generative Model
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. DATA MODELS & HELPERS ---
class Prompt(BaseModel):
    prompt: str

def call_verification_service(code: str) -> dict:
    try:
        response = requests.post("http://localhost:8002/verify", json={"st_code": code})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Verification service is unavailable: {e}")

def generate_from_llm(current_prompt: str) -> dict:
    try:
        response = model.generate_content(current_prompt)
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"❌ ERROR: Failed to parse JSON from LLM response: {e}")
        print(f"Raw AI Output was:\n---\n{response.text}\n---")
        # Return a structured error instead of crashing
        return {"error": "Failed to parse LLM response", "raw_output": response.text}

# --- 3. THE MAIN API ENDPOINT ---
@app.post("/generate")
def generate_and_verify_endpoint(prompt: Prompt):
    print(f"Received prompt: {prompt.prompt}")
    
    initial_prompt = MASTER_PROMPT_V4.replace("{{ USER_PROMPT_GOES_HERE }}", prompt.prompt)
    
    # Initial LLM Call
    print("1. Calling LLM for initial response...")
    generated_json = generate_from_llm(initial_prompt)
    
    # Check for parsing errors from the helper
    if "error" in generated_json:
        raise HTTPException(status_code=500, detail=f"AI returned a malformed response: {generated_json.get('raw_output')}")

    response_type = generated_json.get("response_type")

    # Handle "chat" intent
    if response_type == "chat":
        print("✅ Intent is 'chat'.")
        return {"response_type": "chat", "message": generated_json.get("message")}

    # Handle "generate_code" intent
    elif response_type == "plc_code":
        print("✅ Intent is 'generate_code'. Starting verification loop...")
        
        current_code_json = generated_json
        max_retries = 2 # Let's be more conservative
        for attempt in range(max_retries):
            print(f"\n--- Verification Attempt {attempt + 1} ---")
            
            code_to_verify = current_code_json.get("structured_text")
            if not code_to_verify:
                raise HTTPException(status_code=500, detail="AI failed to provide code.")

            verification_result = call_verification_service(code_to_verify)
            
            if verification_result.get("status") == "success":
                print("✅ Code is valid! Returning result.")
                return {
                    "response_type": "plc_code",
                    "final_json": current_code_json,
                    "verification_status": verification_result
                }
            else:
                print("⚠️ Code is invalid. Constructing correction prompt...")
                error_details = verification_result.get("details", "No details provided.")
                # --- V4 CORRECTION PROMPT ---
                # This prompt is highly specific and reinforces the JSON-only rule.
                correction_prompt = (
                    "The Structured Text code you generated failed syntax verification. "
                    f"The error was: '{error_details}'.\n\n"
                    "Your task is to fix this specific syntax error. Do not explain yourself. Do not apologize. "
                    "Your ONLY output must be the complete, corrected JSON object in the required format, starting with `{` and ending with `}`."
                    f"The original user request was: '{prompt.prompt}'"
                )
                
                print("Retrying with LLM...")
                current_code_json = generate_from_llm(correction_prompt)
                if "error" in current_code_json: # Check for parsing errors on retry
                    raise HTTPException(status_code=500, detail=f"AI returned a malformed response during correction: {current_code_json.get('raw_output')}")


        print("❌ All attempts to generate valid code failed.")
        raise HTTPException(status_code=500, detail="The AI failed to generate syntactically correct code after multiple attempts.")

    # Fallback for unknown response types
    else:
        raise HTTPException(status_code=500, detail=f"AI returned an unknown response type: '{response_type}'")

# --- 4. SERVER LAUNCH ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

