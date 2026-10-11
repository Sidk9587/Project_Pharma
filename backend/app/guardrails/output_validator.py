"""Final output sanity checks; this is defense in depth, not proof of grounding."""

MAX_ANSWER_LENGTH = 20000


def validate_answer(answer: object) -> str | None:
    if not isinstance(answer, str):
        return None
    answer = answer.strip()
    if not answer or len(answer) > MAX_ANSWER_LENGTH:
        return None
    return answer
