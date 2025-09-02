# File: backend/main.py
# The brain of our application

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import requests # To make requests to our other services
import google.generativeai as genai # Assuming you have this configured

# --- Your Gemini AI Setup (from your test script) ---
# genai.configure(api_key="...")
# master_prompt = "..."
# model = genai.GenerativeModel('gemini-1.5-flash')
# ---

app = FastAPI()

class Prompt(BaseModel):
    prompt: str

@app.post("/generate")
def generate_and_verify(prompt: Prompt):
    # STEP 1: Generate code from the LLM (Replace with your actual Gemini call)
    print("1. Generating initial code from LLM...")
    # full_api_prompt = master_prompt.replace("{{ USER_PROMPT_GOES_HERE }}", prompt.prompt)
    # response = model.generate_content(full_api_prompt)
    # generated_json = response.json() # Or however you parse it

    # For testing, let's use placeholder data:
    generated_json = {
        "explanation": "This is a test explanation.",
        "required_variables": "VAR\n  xTest: BOOL;\nEND_VAR",
        "structured_text": "xTest := TRUE;", # This is a valid code
        "verification_notes": "Test notes.",
        "simulation_trace": "Test trace."
    }
    print("2. Code generated.")

    # STEP 2: Automatically validate the generated code
    print("3. Sending generated code to verification service...")
    code_to_verify = generated_json.get("structured_text", "")

    try:
        verification_response = requests.post(
            "http://localhost:8002/verify", 
            json={"st_code": code_to_verify}
        )
        verification_response.raise_for_status() # Raise an exception for bad status codes
        verification_result = verification_response.json()
        print(f"4. Verification result: {verification_result}")

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to verification service: {e}")
        return {"error": "Could not connect to the verification service."}

    # --- NEXT STEP: ADD THE LOOPING LOGIC HERE ---
    # For now, we just return everything

    return {
        "final_json": generated_json,
        "verification_status": verification_result
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)