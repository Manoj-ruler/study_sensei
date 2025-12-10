from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import tempfile
import os

app = FastAPI()

class CodeExecutionRequest(BaseModel):
    code: str
    input_data: str = ""
    language: str = "python" # "python", "javascript"

@app.post("/run")
async def run_code(request: CodeExecutionRequest):
    try:
        # Determine execution command and file extension
        if request.language.lower() in ["javascript", "js", "node"]:
            cmd = ['node']
            suffix = '.js'
        else:
            cmd = ['python']
            suffix = '.py'

        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as temp_code:
            temp_code.write(request.code)
            temp_code_path = temp_code.name

        # Prepare input
        input_data = request.input_data.encode('utf-8')

        # Run the code
        # Timeout after 5 seconds
        full_cmd = cmd + [temp_code_path]
        process = subprocess.Popen(
            full_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False # We handle bytes for input
        )
        
        try:
            stdout, stderr = process.communicate(input=input_data, timeout=5)
            output = stdout.decode('utf-8') + stderr.decode('utf-8')
            
            # success or error, we return the output
            return {
                "output": output,
                "status": "success" if process.returncode == 0 else "failed"
            }
            
        except subprocess.TimeoutExpired:
            process.kill()
            return {"output": "Error: Execution timed out.", "status": "error"}
            
        finally:
            # Clean up
            if os.path.exists(temp_code_path):
                os.remove(temp_code_path)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error executing code: {e}")
        raise HTTPException(status_code=500, detail=str(e))
