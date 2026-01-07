# app/llm/vllm_client.py

from openai import OpenAI


class VLLMClient:
    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:8000/v1",
            api_key="EMPTY",
        )

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            temperature=0,
            top_p=1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content.strip()
