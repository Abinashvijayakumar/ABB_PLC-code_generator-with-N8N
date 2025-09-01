from fastapi import FastAPI
from pydantic import BaseModel
import subprocess

app = FastAPI()

class Code(BaseModel):
    st_code: str

@app.post("/verify")
def verify_code(code: Code):
    # Your logic to save code to a temp file and run matiec
    # ...
    # Return {"status": "success"} or {"status": "error", "details": ...}
    pass