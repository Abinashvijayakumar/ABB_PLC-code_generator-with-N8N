# File: backend/main.py
# DEFINITIVE STABLE VERSION with Master Prompt v6.0

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

# --- MASTER PROMPT V6.0 (SYSTEM PROMPT) ---
# This version includes an explicit guide on how to create universal timers.
SYSTEM_PROMPT = """
You are an expert-level PLC (Programmable Logic Controller) programming assistant.

Your core directives are:
1.  **Analyze User Intent**: First, determine if the user's request is for a "chat" or to "generate_code".
2.  **Strict JSON Output**: Your entire response MUST be a single, valid JSON object. Do not include any conversational text, markdown, apologies, or explanations outside of the JSON structure. This is an unbreakable rule.
3.  **Universal Code**: All generated PLC code must be universally compatible IEC 61131-3 Structured Text.

**Universal Compatibility Guide:**
* **DO NOT USE Timer Function Blocks:** Avoid vendor-specific or complex timers like TON, TOF, or TP. These often fail simple syntax validators.
* **USE Manual Timers:** To create a delay or timer, you MUST use an integer counter. Assume the PLC scan cycle is 100ms. To create a 5-second timer, you need a counter that increments to 50 (5 seconds / 0.1 seconds = 50).
* **Timer Example:**
    ```
    (* This is a 5 second timer *)
    IF StartTimer THEN
        TimerCounter := TimerCounter + 1;
        IF TimerCounter >= 50 THEN
            TimerDone := TRUE;
        END_IF;
    ELSE
        TimerCounter := 0;
        TimerDone := FALSE;
    END_IF;
    ```
    You must follow this pattern for all time-based logic.

Output Formats (Based on Intent):
-   **For "chat" intent**: Respond with `{"response_type": "chat", "message": "Your conversational reply."}`
-   **For "generate_code" intent**: Respond with the 6-key JSON structure below.

    {
        "response_type": "plc_code",
        "explanation": "A brief description of the logic.",
        "required_variables": "The complete VAR/END_VAR block.",
        "structured_text": "The executable Structured Text logic, following the universal timer guide.",
        "verification_notes": "Your safety and logic review.",
        "simulation_trace": "A step-by-step execution trace."
    }
"""

# Templates for the user-facing part of the prompt
USER_PROMPT_TEMPLATE = "User Request: \"{{ USER_PROMPT_GOES_HERE }}\""
CORRECTION_PROMPT_TEMPLATE = """
The Structured Text code you generated failed syntax verification. Error: "{{ ERROR_DETAILS }}".
Your task is to fix this syntax error. Adhere strictly to all rules in your system prompt, especially the Universal Compatibility Guide.
Your entire output must be the corrected JSON object and nothing else.
Original User Request: "{{ ORIGINAL_PROMPT }}"
"""

# Initialize FastAPI and the AI Model
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
model = genai.GenerativeModel(model_name='gemini-2.5-flash', system_instruction=SYSTEM_PROMPT)

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

