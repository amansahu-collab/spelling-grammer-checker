from fastapi import FastAPI
from pydantic import BaseModel
from app.core.evaluator import evaluate_text

app = FastAPI()


class EvaluateRequest(BaseModel):
    summary: str


@app.post("/evaluate")
def evaluate(payload: EvaluateRequest):
    return evaluate_text(payload.summary)
