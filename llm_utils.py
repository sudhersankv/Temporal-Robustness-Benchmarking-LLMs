import os
import requests
from openai import OpenAI
import time

from dotenv import load_dotenv
load_dotenv(override=True)

# Constants for LLM verification; prefix with provider (openai, gemini, groq)
LLM_MODEL = os.getenv("LLM_MODEL", "openai:gpt-4o-mini")
YES_TOKENS = {"yes", "y", "correct", "true"}
NO_TOKENS = {"no", "n", "false", "incorrect"}

# Threshold for fuzzy matching (0 to 1)
FUZZY_THRESHOLD = 0.9

# Throttle requests: max 15 per minute
REQUEST_DELAY = 5  # seconds between calls

def chat_complete(
    prompt: str,
    model_name: str = LLM_MODEL,
) -> str:
    """
    Generate a chat completion string from the specified LLM provider.
    """
    # Choose provider and model
    if ":" in model_name:
        provider, name = model_name.split(":", 1)
    else:
        provider, name = "openai", model_name

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = resp.choices[0].message.content
        time.sleep(REQUEST_DELAY)
        return content

    elif provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set")
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        resp = client.chat.completions.create(
            model=name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = resp.choices[0].message.content
        time.sleep(REQUEST_DELAY)
        return content

    elif provider == "groq":
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise RuntimeError("GROQ_API_KEY not set")
        # Send HTTP POST to Groq API
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": name, "messages": [{"role": "user", "content": prompt}], "temperature": 0}
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        time.sleep(REQUEST_DELAY)
        return content

def llm_verdict(
    question: str,
    gold: str,
    pred: str,
    model_name: str = LLM_MODEL,
) -> bool:
    """
    Ask a language model to verify if pred matches gold.
    Returns True if model responds YES.
    """
    prompt = (
        "You are grading an AI model's answer.\n"
        "Respond with a single word: YES if the model answer is correct, otherwise NO.\n\n"
        f"Question: {question}\n"
        f"Gold answer: {gold}\n"
        f"Model answer: {pred}\n\n"
        "Answer (YES or NO):"
    )

    # Choose provider and model
    if ":" in model_name:
        provider, name = model_name.split(":", 1)
    else:
        provider, name = "openai", model_name

    if provider == "openai":
        # instantiate OpenAI client internally
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = resp.choices[0].message.content

    elif provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set")
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        resp = client.chat.completions.create(
            model=name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = resp.choices[0].message.content

    elif provider == "groq":
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise RuntimeError("GROQ_API_KEY not set")
        # Send HTTP POST to Groq API
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": name, "messages": [{"role": "user", "content": prompt}], "temperature": 0}
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

    else:
        raise ValueError(f"Unknown provider '{provider}' in model_name")

    first = content.strip().lower().split()[0]
    return first in YES_TOKENS
