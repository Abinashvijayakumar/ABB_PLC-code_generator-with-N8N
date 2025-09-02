# File: backend/main.py
# This is the central "brain" or "Orchestrator" of our application.
# The UI will only talk to this file.

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

# Load environment variables from the .env file (e.g., your API key)
load_dotenv()

# Configure the Google Generative AI SDK
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file. Please create a .env file in the root directory.")
    genai.configure(api_key=api_key)
    print("✅ Google AI SDK configured successfully.")
except Exception as e:
    print(f"❌ Error configuring SDK: {e}")
    exit()

# Master Prompt v3.0 with Intent Detection
MASTER_PROMPT_V3 = """
You are a helpful and highly skilled PLC engineering assistant. Your first task is to analyze the user's request and determine their intent. There are two possible intents: "chat" or "generate_code".

1.  **Analyze Intent:**
    * If the user is asking a general question, making a greeting (like "hi", "hello"), or asking for help, the intent is "chat".
    * If the user is describing a logical operation, a machine process, or anything that requires PLC logic (e.g., "turn on a motor", "if sensor A is high"), the intent is "generate_code".

2.  **Generate Response based on Intent:**
    * **If the intent is "chat":**
        Respond with a single JSON object with ONE key: `{"response_type": "chat", "message": "Your friendly, conversational reply goes here."}`. Be helpful and guide the user on how to ask for code. Do NOT generate any PLC code.
    * **If the intent is "generate_code":**
        Respond with a single JSON object with SIX keys as defined below. This is the "PLC Co-pilot" mode.
        - "response_type": Must be the string "plc_code".
        - "explanation": A brief, clear description of the implemented logic.
        - "required_variables": A string containing the complete VAR/END_VAR block.
        - "structured_text": A string containing the executable Structured Text logic.
        - "verification_notes": A string with your safety review and any potential warnings.
        - "simulation_trace": A string describing the step-by-step execution.

**Crucial Rules:**
* Your entire output MUST be a single, valid JSON object. No exceptions.
* Every response must contain the "response_type" key.
---
Analyze the following user request and generate the appropriate JSON response.

**User Request:** "{{ USER_PROMPT_GOES_HERE }}"
"""

# Create FastAPI app
app = FastAPI()

<<<<<<< HEAD
# Add CORS middleware to allow requests from your frontend's local server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


=======
# Add CORS middleware to allow OPTIONS requests (CORS preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

>>>>>>> f647ec493e40e8f3992e91d79f035f4c24209165
# Initialize the Generative Model
model = genai.GenerativeModel('gemini-1.5-flash')


# --- 2. DATA MODELS ---
class Prompt(BaseModel):
    prompt: str


# --- 3. HELPER FUNCTIONS ---
def call_verification_service(code: str) -> dict:
    """Makes a request to our verification microservice."""
    try:
        response = requests.post("http://localhost:8002/verify", json={"st_code": code})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Could not connect to verification service: {e}")
        raise HTTPException(status_code=503, detail=f"Verification service is unavailable: {e}")


def generate_from_llm(current_prompt: str) -> dict:
    """Calls the Gemini API and safely parses the JSON response."""
    try:
        response = model.generate_content(current_prompt)
<<<<<<< HEAD
        cleaned_response = response.text.replace("```json", "").replace("```", "").strip()
=======
        # Remove markdown code fences and extra 'json' if present
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.strip("`").replace("json", "").strip()
        if not cleaned_response:
            raise ValueError("Empty response from LLM.")
>>>>>>> f647ec493e40e8f3992e91d79f035f4c24209165
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"❌ ERROR: Failed to parse JSON from LLM response: {e}")
        print(f"Raw AI Output was:\n---\n{getattr(response, 'text', '')}\n---")
        raise HTTPException(status_code=500, detail="The AI returned a malformed response.")


# --- 4. THE MAIN API ENDPOINT ---
@app.post("/generate")
def generate_and_verify_endpoint(prompt: Prompt):
    """
    Orchestrates the entire process: intent detection, code generation, and self-correction.
    """
    print(f"Received prompt: {prompt.prompt}")
    
    initial_prompt = MASTER_PROMPT_V3.replace("{{ USER_PROMPT_GOES_HERE }}", prompt.prompt)
    
    # Initial LLM Call to Determine Intent
    print("1. Calling LLM to determine intent and generate initial response...")
    generated_json = generate_from_llm(initial_prompt)
    response_type = generated_json.get("response_type")

    # Handle "chat" intent
    if response_type == "chat":
        print("✅ Intent is 'chat'. Returning conversational response.")
        return {"response_type": "chat", "message": generated_json.get("message", "I'm sorry, I had trouble forming a reply.")}

    # Handle "generate_code" intent
    elif response_type == "plc_code":
        print("✅ Intent is 'generate_code'. Starting verification loop...")
        
        max_retries = 3
        for attempt in range(max_retries):
            print(f"\n--- Verification Attempt {attempt + 1} ---")
            
            code_to_verify = generated_json.get("structured_text", "")
            if not code_to_verify:
                raise HTTPException(status_code=500, detail="AI determined intent was code generation but failed to provide code.")

            verification_result = call_verification_service(code_to_verify)
            
            if verification_result.get("status") == "success":
                print("✅ Code is valid! Returning result to UI.")
                return {
                    "response_type": "plc_code",
                    "final_json": generated_json,
                    "verification_status": verification_result,
                    "attempts": attempt + 1
                }
            else: # If verification fails, construct a correction prompt
                print("⚠️ Code is invalid. Constructing correction prompt...")
                error_details = verification_result.get("details", "No details provided.")
                correction_prompt = (
                    f"The Structured Text code you generated failed syntax verification. "
                    f"Error: '{error_details}'.\n\n"
                    f"Please fix this syntax error and provide the complete, corrected JSON object with `response_type: 'plc_code'`. "
                    f"The original user request was: '{prompt.prompt}'"
                )
                print("Retrying with LLM...")
                generated_json = generate_from_llm(correction_prompt)

        print("❌ All attempts to generate valid code failed.")
        raise HTTPException(status_code=500, detail="The AI failed to generate syntactically correct code after multiple attempts.")

    # Fallback for unknown response types
    else:
        print(f"❌ Unknown response_type from AI: {response_type}")
        raise HTTPException(status_code=500, detail="The AI returned an unknown response type.")

# --- 5. SERVER LAUNCH ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
