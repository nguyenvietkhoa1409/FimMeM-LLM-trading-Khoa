# Debug script to identify subprocess execution issues

import os
import json
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

def debug_subprocess_execution():
    """Debug the subprocess execution that's causing the 401 error"""
    
    print("=== SUBPROCESS EXECUTION DEBUG ===")
    
    # 1. Check paths
    together_venv_path = os.path.join("venv_together", "Scripts", "python.exe")
    together_script_path = "together_chat.py"
    
    print(f"1. Python executable path: {together_venv_path}")
    print(f"   Exists: {os.path.exists(together_venv_path)}")
    
    print(f"2. Together script path: {together_script_path}")
    print(f"   Exists: {os.path.exists(together_script_path)}")
    
    # 2. Check if the hardcoded paths in your code are correct
    hardcoded_python = r"D:\Data science research\FinMem-LLM-StockTrading\venv_together\Scripts\python.exe"
    hardcoded_script = r"D:\Data science research\FinMem-LLM-StockTrading\puppy\together_chat.py"
    
    print(f"3. Hardcoded Python path: {hardcoded_python}")
    print(f"   Exists: {os.path.exists(hardcoded_python)}")
    
    print(f"4. Hardcoded script path: {hardcoded_script}")
    print(f"   Exists: {os.path.exists(hardcoded_script)}")
    
    # 3. Test environment variable passing
    api_key = os.environ.get("TOGETHER_API_KEY", "")
    print(f"5. Current API key: {api_key[:10]}..." if api_key else "No API key")
    
    # 4. Test the actual subprocess call
    print("\n6. Testing subprocess call...")
    test_subprocess_call(api_key)
    
    return hardcoded_python, hardcoded_script

def test_subprocess_call(api_key):
    """Test the actual subprocess call that's failing"""
    
    # Prepare environment
    env = os.environ.copy()
    env["TOGETHER_API_KEY"] = api_key
    
    # Prepare input data
    input_data = json.dumps([
        {"role": "system", "content": "You are a helpful assistant only capable of communicating with valid JSON, and no other text."},
        {"role": "user", "content": "Hello, this is a test."}
    ])
    
    # Test with hardcoded paths (as in your original code)
    hardcoded_python = r"D:\Data science research\FinMem-LLM-StockTrading\venv_together\Scripts\python.exe"
    hardcoded_script = r"D:\Data science research\FinMem-LLM-StockTrading\puppy\together_chat.py"
    
    print(f"   Input data length: {len(input_data)}")
    print(f"   Environment TOGETHER_API_KEY: {env.get('TOGETHER_API_KEY', 'NOT SET')[:10]}...")
    
    try:
        result = subprocess.run(
            [hardcoded_python, hardcoded_script],
            input=input_data,
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=60
        )
        
        print(f"   Return code: {result.returncode}")
        print(f"   STDOUT: {result.stdout}")
        print(f"   STDERR: {result.stderr}")
        
        if result.returncode != 0:
            print("   ❌ Subprocess failed!")
            analyze_subprocess_failure(result)
        else:
            print("   ✅ Subprocess succeeded!")
            
    except subprocess.TimeoutExpired:
        print("   ❌ Subprocess timed out!")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def analyze_subprocess_failure(result):
    """Analyze why the subprocess failed"""
    print("\n=== FAILURE ANALYSIS ===")
    
    stderr = result.stderr.lower() if result.stderr else ""
    stdout = result.stdout.lower() if result.stdout else ""
    
    if "401" in stderr or "unauthorized" in stderr:
        print("- Issue: 401 Unauthorized error")
        print("- Cause: API key not reaching the subprocess or invalid in subprocess context")
        
    if "module not found" in stderr or "importerror" in stderr:
        print("- Issue: Missing Python modules")
        print("- Cause: Virtual environment not properly activated or missing packages")
        
    if "file not found" in stderr or "no such file" in stderr:
        print("- Issue: Script file not found")
        print("- Cause: Incorrect path to together_chat.py")
        
    if not result.stdout and not result.stderr:
        print("- Issue: No output at all")
        print("- Cause: Python executable not found or script crashed immediately")

# Fixed version of the subprocess call in your chat.py
def create_fixed_subprocess_method():
    """Create a fixed version of the run_together_subprocess method"""
    
    fixed_method = '''
def run_together_subprocess(self, prompt: str) -> str:
    try:
        # Get API key and validate
        api_key = os.environ.get("TOGETHER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("TOGETHER_API_KEY environment variable not set")
        
        print(f"DEBUG: API key starts with: {api_key[:10]}...")
        
        # Set up environment - CRITICAL: Make sure to pass the API key
        env = os.environ.copy()
        env["TOGETHER_API_KEY"] = api_key
        
        # Use the hardcoded paths (but make them configurable in the future)
        python_path = r"D:\\Data science research\\FinMem-LLM-StockTrading\\venv_together\\Scripts\\python.exe"
        script_path = r"D:\\Data science research\\FinMem-LLM-StockTrading\\puppy\\together_chat.py"
        
        # Verify paths exist
        if not os.path.exists(python_path):
            raise RuntimeError(f"Python executable not found: {python_path}")
        if not os.path.exists(script_path):
            raise RuntimeError(f"Script not found: {script_path}")
        
        # Prepare input
        input_data = json.dumps([
            {"role": "system", "content": "You are a helpful assistant only capable of communicating with valid JSON, and no other text."},
            {"role": "user", "content": prompt}
        ])
        
        print(f"DEBUG: Calling subprocess with paths:")
        print(f"  Python: {python_path}")
        print(f"  Script: {script_path}")
        print(f"  Input length: {len(input_data)}")
        
        result = subprocess.run(
            [python_path, script_path],
            input=input_data,
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception on non-zero exit
            env=env,
            timeout=120,
            cwd=os.path.dirname(script_path)  # Set working directory
        )
        
        print(f"DEBUG: Subprocess completed:")
        print(f"  Return code: {result.returncode}")
        print(f"  STDOUT: {result.stdout}")
        print(f"  STDERR: {result.stderr}")
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise RuntimeError(f"Together subprocess failed (code {result.returncode}): {error_msg}")
        
        return result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("Together API subprocess timed out after 2 minutes")
    except Exception as e:
        print(f"DEBUG: Exception in run_together_subprocess: {e}")
        raise RuntimeError(f"Error running Together subprocess: {str(e)}")
'''
    
    return fixed_method

def test_direct_script_execution():
    """Test running the together_chat.py script directly"""
    print("\n=== DIRECT SCRIPT EXECUTION TEST ===")
    
    script_path = r"D:\Data science research\FinMem-LLM-StockTrading\puppy\together_chat.py"
    python_path = r"D:\Data science research\FinMem-LLM-StockTrading\venv_together\Scripts\python.exe"
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return
        
    if not os.path.exists(python_path):
        print(f"❌ Python executable not found: {python_path}")
        return
    
    # Test with environment variable
    test_input = json.dumps([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello"}
    ])
    
    try:
        env = os.environ.copy()
        env["TOGETHER_API_KEY"] = os.environ.get("TOGETHER_API_KEY", "")
        
        result = subprocess.run(
            [python_path, script_path],
            input=test_input,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        
        print(f"Direct execution result:")
        print(f"  Return code: {result.returncode}")
        print(f"  STDOUT: {result.stdout}")
        print(f"  STDERR: {result.stderr}")
        
    except Exception as e:
        print(f"❌ Direct execution failed: {e}")

if __name__ == "__main__":
    debug_subprocess_execution()
    test_direct_script_execution()
    
    print("\n=== RECOMMENDED ACTIONS ===")
    print("1. Check if the hardcoded paths in your code are correct")
    print("2. Ensure the virtual environment has all required packages")
    print("3. Test the together_chat.py script directly")
    print("4. Add more debugging to see what's happening in the subprocess")
    print("5. Consider using relative paths instead of hardcoded absolute paths")