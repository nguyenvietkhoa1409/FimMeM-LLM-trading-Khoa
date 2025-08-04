# together_chat_client.py
import os
import httpx

class TogetherChat:
    def __init__(self, model: str, endpoint: str = None, api_key: str = None):
        self.api_key = api_key or os.environ.get("TOGETHER_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError("No Together API key provided!")

        self.model = model
        self.endpoint = endpoint or "https://api.together.xyz/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_completion(self, messages: list, **kwargs) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.95),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }

        response = httpx.post(self.endpoint, headers=self.headers, json=payload, timeout=60)

        if response.status_code == 401:
            raise RuntimeError("Unauthorized: Check your Together API key.")
        if response.status_code != 200:
            raise RuntimeError(f"API call failed: {response.status_code} - {response.text}")

        data = response.json()
        return data["choices"][0]["message"]["content"]

if __name__ == "__main__":
    import sys
    import json

    messages = json.loads(sys.stdin.read())
    chat = TogetherChat(model="mistralai/Mixtral-8x7B-Instruct-v0.1")
    completion = chat.get_completion(messages)
    print(completion)
