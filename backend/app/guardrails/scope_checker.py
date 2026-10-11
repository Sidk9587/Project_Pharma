"""Shared validation for question text accepted by both chat transports."""

MAX_QUESTION_LENGTH = 2000


def validate_question(question: object) -> str:
    if not isinstance(question, str):
        raise ValueError("Question must be a string.")
    normalized = question.strip()
    if not normalized:
        raise ValueError("Question must not be empty.")
    if len(normalized) > MAX_QUESTION_LENGTH:
        raise ValueError(f"Question must be at most {MAX_QUESTION_LENGTH} characters.")
    return normalized
