# File: backend/scripts/verify_st.py
# FINAL CORRECTED VERSION FOR WINDOWS

import subprocess
import tempfile
import os

def verify_structured_text(st_code: str) -> dict:
    """
    Verifies a string of Structured Text using the iec2c.exe compiler on Windows.
    This version uses a direct path and the correct executable name.
    """
    try:
        # Construct the full path to the matiec/OpenPLC directory
        # The folder is called 'matiec' even if the exe is 'iec2c.exe'
        matiec_dir = os.path.join(os.path.expanduser("~"), "OpenPLC_Editor", "matiec")
        
        # --- THE CRITICAL FIX IS HERE ---
        # We are now looking for 'iec2c.exe'
        executable_name = "iec2c.exe"
        executable_path = os.path.join(matiec_dir, executable_name)
        lib_path = os.path.join(matiec_dir, "lib")

        if not os.path.isfile(executable_path):
            return {"status": "error", "details": f"{executable_name} not found at {executable_path}. Is OpenPLC Editor installed correctly?"}
        
        if not os.path.isdir(lib_path):
            return {"status": "error", "details": f"MATIEC library not found at {lib_path}."}
    
    except Exception as e:
         return {"status": "error", "details": f"Could not construct paths. Error: {e}"}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.st', delete=False) as tmp:
        tmp.write(st_code)
        tmp_filename = tmp.name

    try:
        # The command now uses the correct executable path
        command = [executable_path, "-I", lib_path, tmp_filename]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        return {"status": "success", "details": "Syntax OK"}

    except subprocess.CalledProcessError as e:
        return {"status": "error", "details": e.stderr}
    
    except FileNotFoundError:
        return {"status": "error", "details": f"The executable was not found at the specified path: {executable_path}"}

    finally:
        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)

# --- Example Usage for Testing ---
if __name__ == "__main__":
    valid_code = "PROGRAM main\n  VAR\n    StartButton AT %IX0.0 : BOOL;\n  END_VAR\n  POU_body\n    ; (* A comment *) \n  END_POU\nEND_PROGRAM"
    invalid_code = "PROGRAM main\n  Motor = StartButton;\nEND_PROGRAM"

    print("--- Testing Valid Code ---")
    print(verify_structured_text(valid_code))
    
    print("\n--- Testing Invalid Code ---")
    print(verify_structured_text(invalid_code))