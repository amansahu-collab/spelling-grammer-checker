# app/config.py

# Grammar scoring thresholds
GRAMMAR_BASE_SCORE_THRESHOLDS = {
    "4": 1,
    "3": 4,
    "2": 8,
    "1": 12,
}

# Spelling score thresholds
SPELLING_THRESHOLDS = {
    4: 0,
    3: 2,
    2: 5,
    1: 9,
}

# LLM behavior
LLM_TEMPERATURE = 0
