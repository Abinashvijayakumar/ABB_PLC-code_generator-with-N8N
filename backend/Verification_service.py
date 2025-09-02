# File: backend/verification_service.py
# This creates the API endpoint for the frontend to call.

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Import your working verification function from the other file
from scripts.verify_st import verify_structured_text

app = FastAPI()

# This defines the structure of the incoming request body
class CodeToVerify(BaseModel):
    st_code: str

@app.post("/verify")
def handle_verification_request(code: CodeToVerify):
    """
    Receives ST code from a POST request, validates it using the
    verify_structured_text function, and returns the result.
    """
    result = verify_structured_text(code.st_code)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)