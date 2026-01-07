from pydantic import BaseModel
from typing import List, Dict, Any


class GrammarExplanation(BaseModel):
    type: str
    text_span: str
    description: str


class GrammarExplanationResponse(BaseModel):
    errors: List[GrammarExplanation]


class GrammarResponse(BaseModel):
    score: int
    details: List[Dict[str, Any]]
    explanation: GrammarExplanationResponse


class SpellingResponse(BaseModel):
    total_words: int
    misspelled_count: int
    misspelled_words: List[str]
    spelling_score: int


class EvaluateResponse(BaseModel):
    grammar: GrammarResponse
    spelling: SpellingResponse
