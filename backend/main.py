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
        raise ValueError("GOOGLE_API_KEY not found in .env file")
    genai.configure(api_key=api_key)
    print("✅ Google AI SDK configured successfully.")
except Exception as e:
    print(f"❌ Error configuring SDK: {e}")
    # Exit if the SDK can't be configured, as the app is useless without it.
    exit()

# The definitive Master Prompt for generating structured JSON output
MASTER_PROMPT = """
You are a top-tier industrial automation safety and logic engineer with 25 years of experience. Your specialty is writing universally compatible IEC 61131-3 Structured Text that is safe, efficient, and well-documented.

Your task is to convert a user's natural language request into a complete, structured JSON object.

You MUST adhere to the following rules:
1.  *Strict JSON Output:* The entire response MUST be a single, valid JSON object. Do not include any text, explanation, or markdown formatting outside of this JSON block.
2.  *Analyze & Declare:* Identify all required variables and create a complete VAR/END_VAR block. Use logical, UpperCamelCase variable names.
3.  *Generate Code:* Write clean, well-commented Structured Text logic.
4.  *Verify Logic:* After generating the code, perform a logical safety review. Check for race conditions, unsafe states, or potential infinite loops. Summarize your findings.
5.  *Simulate Execution:* Provide a brief, step-by-step trace of how the logic would execute with a simple, true-case example.

The JSON object must contain these five keys:
- "explanation": A brief, clear description of the implemented logic.
- "required_variables": A string containing the complete VAR/END_VAR block.
- "structured_text": A string containing the executable logic.
- "verification_notes": A string with your safety review and any potential warnings.
- "simulation_trace": A string describing the step-by-step execution.
---
Convert the following user request into the specified JSON format.

*User Request:* "{{ USER_PROMPT_GOES_HERE }}"
"""

# Create FastAPI app
app = FastAPI()

# Add CORS middleware to allow OPTIONS requests (CORS preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Generative Model
model = genai.GenerativeModel('gemini-1.5-flash')


# --- 2. DATA MODELS ---

# Defines the expected structure of a request from the UI
class Prompt(BaseModel):
    prompt: str


# --- 3. HELPER FUNCTIONS ---

def call_verification_service(code: str) -> dict:
    """Makes a request to our verification microservice."""
    try:
        response = requests.post(
            "http://localhost:8002/verify",
            json={"st_code": code}
        )
        response.raise_for_status()  # Raises an exception for HTTP errors (like 404, 500)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Could not connect to verification service: {e}")
        # This is a critical failure, we raise an HTTPException to inform the UI
        raise HTTPException(status_code=503, detail=f"Verification service is unavailable: {e}")


def generate_code_from_llm(current_prompt: str) -> dict:
    """Calls the Gemini API and parses the JSON response."""
    try:
        response = model.generate_content(current_prompt)
        # Remove markdown code fences and extra 'json' if present
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.strip("`").replace("json", "").strip()
        if not cleaned_response:
            raise ValueError("Empty response from LLM.")
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"❌ ERROR: Failed to parse JSON from LLM response: {e}")
        print(f"Raw AI Output was:\n---\n{getattr(response, 'text', '')}\n---")
        raise HTTPException(status_code=500, detail="The AI returned a malformed response.")


# --- 4. THE MAIN API ENDPOINT ---

@app.post("/generate")
def generate_and_verify_endpoint(prompt: Prompt):
    """
    This is the main endpoint the UI calls. It orchestrates the entire process:
    1. Generates code from the LLM.
    2. Automatically verifies the code.
    3. If verification fails, it asks the LLM to correct the code (the loop).
    4. Returns the final, validated code to the UI.
    """
    print(f"Received prompt: {prompt.prompt}")
    
    # Construct the initial prompt for the LLM
    current_prompt = MASTER_PROMPT.replace("{{ USER_PROMPT_GOES_HERE }}", prompt.prompt)
    
    # The self-correction loop (try up to 3 times)
    max_retries = 3
    for attempt in range(max_retries):
        print(f"\n--- Attempt {attempt + 1} of {max_retries} ---")
        
        # Step 1: Generate code from the LLM
        print("1. Generating code from LLM...")
        generated_json = generate_code_from_llm(current_prompt)
        code_to_verify = generated_json.get("structured_text", "")
        
        if not code_to_verify:
            print("LLM did not return any code to verify. Retrying...")
            current_prompt = f"The previous attempt failed because you did not provide any code in the 'structured_text' field. Please try again and strictly follow the JSON format. The original user request was: '{prompt.prompt}'"
            continue # Skip to the next iteration of the loop

        # Step 2: Automatically validate the generated code
        print("2. Verifying generated code...")
        verification_result = call_verification_service(code_to_verify)
        print(f"3. Verification status: {verification_result.get('status')}")

        # Step 3: The Decision Point
        if verification_result.get("status") == "success":
            print("✅ Code is valid! Returning result to UI.")
            return {
                "final_json": generated_json,
                "verification_status": verification_result,
                "attempts": attempt + 1
            }
        else:
            # If code is invalid, prepare for the next loop iteration
            print("⚠ Code is invalid. Constructing correction prompt...")
            error_details = verification_result.get("details", "No details provided.")
            current_prompt = (
                f"The code you previously generated failed the MATIEC syntax verification. "
                f"Error details: '{error_details}'.\n\n"
                f"Please analyze the error and the code, fix the issue, and provide the complete, corrected JSON object. "
                f"The original user request was: '{prompt.prompt}'"
            )

    # If the loop finishes without success
    print("❌ All attempts to generate valid code failed.")
    raise HTTPException(status_code=500, detail="The AI failed to generate syntactically correct code after multiple attempts.")


# --- 5. SERVER LAUNCH ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)