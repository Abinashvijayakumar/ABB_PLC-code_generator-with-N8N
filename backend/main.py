import os
import json
import requests
import uvicorn
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

# Define the data model for the incoming request from the React UI
class GenerationRequest(BaseModel):
    prompt: str

# Create the FastAPI app instance
app = FastAPI()

# A simple root endpoint to check if the API is running
@app.get("/")
def read_root():
    return {"status": "PLC AI Generator API is running"}

# The main endpoint for code generation
@app.post("/api/generate")
def generate_code(request: GenerationRequest):
    # Get the n8n webhook URL from Member 1
    # For now, we can hardcode it. Later, we'll use environment variables.
    n8n_webhook_url = "http://host.docker.internal:5678/webhook/..." # Use the URL from Member 1

    try:
        # Forward the prompt to the n8n workflow
        response = requests.post(n8n_webhook_url, json={"prompt": request.prompt})
        
        # Check for a successful response from n8n
        if response.status_code == 200:
            # Return the data from n8n directly to the React frontend
            return response.json()
        else:
            return {"error": "Failed to get response from n8n workflow", "details": response.text}

    except Exception as e:
        return {"error": "An exception occurred", "details": str(e)}