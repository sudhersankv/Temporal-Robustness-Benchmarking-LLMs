# prompt_builder.py
"""Compose the evaluation prompt for the model‑under‑test.

The prompt structure is deliberately minimal to reduce variance:

    <SYSTEM_PROMPT>

    <FACT_SET>

    Question: <question_text>
    Answer:

The model is expected to output a **single line** answer (no punctuation
constraint) immediately following `Answer:`.
"""
from __future__ import annotations

SYSTEM_PROMPT = (
    "You are a highly accurate temporal reasoner. Using ONLY the facts provided, "
    "answer the question. Respond with a concise answer—do not explain your reasoning."
)

__all__ = ["build_prompt", "SYSTEM_PROMPT"]


def build_prompt(fact_set: str, question_text: str) -> str:
    """Return the complete prompt string."""
    return f"{SYSTEM_PROMPT}\n\n{fact_set}\n\nQuestion: {question_text}\nAnswer:"
