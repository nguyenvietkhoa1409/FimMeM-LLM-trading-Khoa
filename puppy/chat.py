import os
import json
import subprocess
from abc import ABC
from typing import Callable, Union, Dict, Any
from dotenv import load_dotenv

import httpx

load_dotenv(dotenv_path=".env")

class LongerThanContextError(Exception):
    pass

def build_llama2_prompt(messages):
    """
    Builds prompt for LLaMA2-style chat models (TGI-style serving).
    """
    startPrompt = "<s>[INST] "
    endPrompt = " [/INST]"
    conversation = []
    for index, message in enumerate(messages):
        if message["role"] == "system" and index == 0:
            conversation.append(f"<<SYS>>\n{message['content']}\n<</SYS>>\n\n")
        elif message["role"] == "user":
            conversation.append(message["content"].strip())
        else:  # Assistant role
            conversation.append(f" [/INST] {message['content'].strip()}</s><s>[INST] ")

    return startPrompt + "".join(conversation) + endPrompt

class ChatOpenAICompatible(ABC):
    """
    Unified interface for calling different chat-based models:
    - OpenAI GPT
    - Gemini Pro
    - TGI (LLaMA-style)
    - Together API (DeepSeek or other hosted LLMs)
    """

    def __init__(
        self,
        end_point: str,
        model="gemini-pro",
        system_message: str = "You are a helpful assistant.",
        other_parameters: Union[Dict[str, Any], None] = None,
        together_script_path : str = "together_chat.py",
        together_venv_path: str = "venv_together",
    ):
        api_key = os.environ.get("OPENAI_API_KEY", "-")
        self.end_point = end_point
        self.model = model
        self.system_message = system_message
        self.together_script_path = together_script_path
        self.together_venv_path =os.path.join(together_venv_path, "Scripts", "python.exe")
        
        self.other_parameters = {} if other_parameters is None else other_parameters

        if model.startswith("gemini-pro"):
            proc_result = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True)
            access_token = proc_result.stdout.strip()
            self.headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

        elif model.startswith("tgi"):
            self.headers = {
                "Content-Type": "application/json"
            }

        elif model.startswith("deepseek"):
            self.headers = None

        else:  # Fallback for OpenAI-compatible endpoints
            self.headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

    def parse_response(self, response: httpx.Response) -> str:
        """
        Parse API responses into plain text depending on model type.
        """
        if self.model.startswith("gpt"):
            return response.json()["choices"][0]["message"]["content"]

        elif self.model.startswith("gemini-pro"):
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]

        elif self.model.startswith("tgi"):
            return response.json()["generated_text"]

        else:
            raise NotImplementedError(f"Model {self.model} not implemented")

    def run_together_subprocess(self, prompt: str) -> str:
        try:
            env = os.environ.copy()
            env["TOGETHER_API_KEY"] = os.environ.get("TOGETHER_API_KEY", "")
            result = subprocess.run(
                [r"D:\Data science research\FinMem-LLM-StockTrading\venv_together\Scripts\python.exe", r"D:\Data science research\FinMem-LLM-StockTrading\puppy\together_chat.py"],
                input=json.dumps([
    {"role": "system", "content": "You are a helpful assistant only capable of communicating with valid JSON, and no other text."},
    {"role": "user", "content": prompt}
                ]),
                capture_output=True,
                text=True,
                check=True,
                env = env 
            )
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            print("Return code:", result.returncode)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error running Together subprocess: {e.stderr.strip()}")
        
    def guardrail_endpoint(self) -> Callable:
        def end_point(input: str, **kwargs) -> str:
            input_str = [
                {"role": "system", "content": "You are a helpful assistant only capable of communicating with valid JSON, and no other text."},
                {"role": "user", "content": f"{input}"},
            ]

            if self.model.startswith("gemini-pro"):
                input_prompts = {
                    "role": "USER",
                    "parts": {"text": input_str[1]["content"]},
                }
                payload = {
                    "contents": input_prompts,
                    "generation_config": {
                        "temperature": 0.2,
                        "top_p": 0.1,
                        "top_k": 16,
                        "max_output_tokens": 2048,
                        "candidate_count": 1,
                        "stop_sequences": [],
                    },
                    "safety_settings": {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_LOW_AND_ABOVE",
                    },
                }
                response = httpx.post(self.end_point, headers=self.headers, json=payload, timeout=600.0)

            elif self.model.startswith("tgi"):
                llama_input_str = build_llama2_prompt(input_str)
                payload = {
                    "inputs": llama_input_str,
                    "parameters": {
                        "do_sample": True,
                        "top_p": 0.6,
                        "temperature": 0.8,
                        "top_k": 50,
                        "max_new_tokens": 256,
                        "repetition_penalty": 1.03,
                        "stop": ["</s>"],
                    },
                }
                response = httpx.post(self.end_point, headers=self.headers, json=payload, timeout=600.0)

            elif self.model.startswith("together"):
                return self.run_together_subprocess(input)

            else:
                payload = {
                    "model": self.model,
                    "messages": input_str,
                }
                payload.update(self.other_parameters)
                response = httpx.post(
                    self.end_point, headers=self.headers, json=payload, timeout=600.0
                )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if (response.status_code == 422) and ("must have less than" in response.text):
                    raise LongerThanContextError
                else:
                    raise e

            return self.parse_response(response)

        return end_point