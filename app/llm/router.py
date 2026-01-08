# app/llm/router.py

import subprocess
from llm.vllm_client import VLLMClient
from llm.ollama_client import OllamaClient


def gpu_available() -> bool:
    try:
        subprocess.run(
            ["nvidia-smi"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception:
        return False


class LLMRouter:
    def __init__(self):
        if gpu_available():
            self.client = VLLMClient()
        else:
            self.client = OllamaClient()

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        return self.client.chat(system_prompt, user_prompt)
