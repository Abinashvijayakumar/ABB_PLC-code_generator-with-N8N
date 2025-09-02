# File: backend/main.py
# DEFINITIVE STABLE VERSION with Master Prompt v7.0 - The Indoctrination Prompt

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

# --- MASTER PROMPT V7.0 (SYSTEM PROMPT) ---
# This version uses aggressive, undeniable instructions to force compliance.
SYSTEM_PROMPT = """
You are an expert-level PLC (Programmable Logic Controller) programming assistant with one critical limitation: your target environment uses a very basic syntax validator that does not support advanced function blocks. You must generate code that is simple and universally compliant above all else.

Your core directives are:
1.  **Analyze User Intent**: Determine if the user's request is for "chat" or "generate_code".
2.  **Strict JSON Output**: Your entire response MUST be a single, valid JSON object. Do not include any text or markdown outside of the JSON structure. This is an unbreakable rule.
3.  **Universal Code Mandate**: All generated PLC code must be universally compatible IEC 61131-3 Structured Text.

**MANDATORY UNIVERSAL COMPATIBILITY GUIDE:**
* **FORBIDDEN FUNCTIONS**: You are strictly forbidden from using any pre-built timer function blocks like TON, TOF, or TP. Their use is a critical failure.
* **REQUIRED TIMER PATTERN**: For ANY and ALL time-based logic (delays, intervals, sequences), you MUST and WILL ONLY use the following manual integer counter pattern. This is not a suggestion; it is the only valid way to create a timer in your target environment.
* **The Only Acceptable Timer Example:**
    ```
    (* This is a 5 second timer, assuming a 100ms scan cycle *)
    IF StartTimer THEN
        TimerCounter := TimerCounter + 1;
        IF TimerCounter >= 50 THEN (* 5s / 0.1s = 50 cycles *)
            TimerDone := TRUE;
        END_IF;
    ELSE
        TimerCounter := 0;
        TimerDone := FALSE;
    END_IF;
    ```
    Failure to use this exact pattern for timers will result in a verification error.

Output Formats (Based on Intent):
-   **For "chat" intent**: `{"response_type": "chat", "message": "Your conversational reply."}`
-   **For "generate_code" intent**: The 6-key JSON structure below.
    {
        "response_type": "plc_code",
        "explanation": "...",
        "required_variables": "...",
        "structured_text": "...",
        "verification_notes": "...",
        "simulation_trace": "..."
    }
"""

# Templates for the user-facing part of the prompt
USER_PROMPT_TEMPLATE = "User Request: \"{{ USER_PROMPT_GOES_HERE }}\""
CORRECTION_PROMPT_TEMPLATE = """
The Structured Text code you generated failed syntax verification. Error: "{{ ERROR_DETAILS }}".
This failure is likely because you violated the MANDATORY UNIVERSAL COMPATIBILITY GUIDE.
Re-read your system instructions. You MUST use the manual integer counter pattern for all timers.
Your task is to fix the code to be 100% compliant. Your entire output must be the corrected JSON object and nothing else.
Original User Request: "{{ ORIGINAL_PROMPT }}"
"""

# Initialize FastAPI and the AI Model
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)

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

def generate_from_llm(user_prompt: str) -> dict:
    try:
        response = model.generate_content(user_prompt)
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"❌ ERROR: Failed to parse JSON from LLM response: {e}")
        print(f"Raw AI Output was:\n---\n{response.text}\n---")
        return {"error": "Failed to parse LLM response", "raw_output": response.text}

# --- 3. THE MAIN API ENDPOINT ---
@app.post("/generate")
def generate_and_verify_endpoint(prompt: Prompt):
    print(f"Received prompt: {prompt.prompt}")
    
    user_prompt = USER_PROMPT_TEMPLATE.replace("{{ USER_PROMPT_GOES_HERE }}", prompt.prompt)
    
    print("1. Calling LLM for initial response...")
    generated_json = generate_from_llm(user_prompt)
    
    if "error" in generated_json:
        raise HTTPException(status_code=500, detail=f"AI returned a malformed response: {generated_json.get('raw_output')}")

    response_type = generated_json.get("response_type")

    if response_type == "chat":
        print("✅ Intent is 'chat'.")
        return {"response_type": "chat", "message": generated_json.get("message")}

    elif response_type == "plc_code":
        print("✅ Intent is 'generate_code'. Starting verification loop...")
        
        current_code_json = generated_json
        max_retries = 2
        for attempt in range(max_retries):
            print(f"\n--- Verification Attempt {attempt + 1} of {max_retries} ---")
            
            code_to_verify = current_code_json.get("structured_text")
            if not code_to_verify:
                raise HTTPException(status_code=500, detail="AI failed to provide code in 'structured_text' field.")

            verification_result = call_verification_service(code_to_verify)
            
            if verification_result.get("status") == "success":
                print("✅ Code is valid! Returning result.")
                return {"response_type": "plc_code", "final_json": current_code_json, "verification_status": verification_result}
            else:
                print("⚠️ Code is invalid. Constructing correction prompt...")
                error_details = verification_result.get("details", "No details provided.")
                correction_prompt = CORRECTION_PROMPT_TEMPLATE.replace("{{ ERROR_DETAILS }}", error_details).replace("{{ ORIGINAL_PROMPT }}", prompt.prompt)
                
                print("Retrying with LLM...")
                current_code_json = generate_from_llm(correction_prompt)
                if "error" in current_code_json:
                    raise HTTPException(status_code=500, detail=f"AI returned a malformed response during correction: {current_code_json.get('raw_output')}")

        print("❌ All attempts to generate valid code failed.")
        raise HTTPException(status_code=500, detail="The AI failed to generate syntactically correct code after multiple attempts.")

    else:
        raise HTTPException(status_code=500, detail=f"AI returned an unknown response type: '{response_type}'")

# --- 4. SERVER LAUNCH ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# File: backend/main.py