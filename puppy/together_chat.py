# together_chat_client.py
import os
import httpx
from together import Together

class TogetherChat:
    def __init__(self, model: str, endpoint: str = None, api_key: str = None):
        self.api_key = api_key or os.environ.get("TOGETHER_API_KEY", "")
        self.model = model
        self.client = Together(api_key=self.api_key)
        self.endpoint = endpoint  # optional, for custom endpoint if needed

    def get_completion(self, messages: list, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            top_p=kwargs.get("top_p", 0.95),
            max_tokens=kwargs.get("max_tokens", 1024),
            stop=kwargs.get("stop", None),
        )
        return response.choices[0].message.content

if __name__ == "__main__":
    import sys 
    import json 
    messages = json.loads(sys.stdin.read())
    chat = TogetherChat(model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free")
    compeltion = chat.get_completion(messages)
    