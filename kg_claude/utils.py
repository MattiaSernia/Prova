import re
import time
import logging
import ollama
from math import ceil


def ollama_chat(model: str, messages: list, max_retries: int = 3, **kwargs) -> dict:
    for attempt in range(max_retries):
        try:
            return ollama.chat(model, messages=messages, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logging.warning(f"Ollama call failed (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(2 ** attempt)


def uri_to_label(uri) -> str:
    s = str(uri)
    s = s.rsplit("#", 1)[-1] if "#" in s else s.rsplit("/", 1)[-1]
    return s.replace("_", " ")


def sentence_split(text: str, chunk_dim:int) -> list:
    abbrev = r"\b(Mr|Mrs|Dr|Prof|vs|etc|Jr|Sr|Fig|al)\."
    text = re.sub(abbrev, r"\1<DOT>", text)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text)
    sentences = [s.replace("<DOT>", ".").strip() for s in sentences]
    if chunk_dim==0:
        dim=1
    else:
        dim=ceil(len(sentences)*(chunk_dim/100))
    sentences= [" ".join(sentences[i:i+dim]) for i in range(0, len(sentences), dim)]
    return [s for s in sentences if s]
