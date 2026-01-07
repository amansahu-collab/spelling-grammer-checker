# app/schemas/request.py

from pydantic import BaseModel


class EvaluateRequest(BaseModel):
    summary: str
