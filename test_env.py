import os
from dotenv import load_dotenv
import subprocess
import json

# Step 1: Load .env into environment
load_dotenv(dotenv_path=".env")

# Step 2: Verify key is available
api_key = os.getenv("TOGETHER_API_KEY")
if not api_key:
    raise EnvironmentError("TOGETHER_API_KEY is not set in the environment!")

print("✅ Parent environment API key prefix:", api_key[:6] + "...")

# Step 3: Prepare test message
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
]

# Step 4: Run subprocess
env = os.environ.copy()

result = subprocess.run(
    [r"D:\Data science research\FinMem-LLM-StockTrading\venv_together\Scripts\python.exe", r"D:\Data science research\FinMem-LLM-StockTrading\puppy\together_chat.py"],
    input=json.dumps(messages),
    text=True,
    capture_output=True,
    env=env
)

# Step 5: Show results
print("\n📤 Subprocess STDOUT:\n", result.stdout)
print("\n⚠️ Subprocess STDERR:\n", result.stderr)
print("\n🔁 Subprocess return code:", result.returncode)
