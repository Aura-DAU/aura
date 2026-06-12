from transformers import AutoTokenizer
from config import (MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def split_section(text):
    """
    Split section into 256-token chunks with overlap.
    """
    
    tokens = tokenizer.encode(text, add_special_tokens=False, truncation=False)
    
    if len(tokens) <= CHUNK_SIZE:
        return [text]

    chunks = []

    start = 0

    while start < len(tokens):
        end = start + CHUNK_SIZE
        chunk_tokens = tokens[start:end]

        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)

        chunks.append(chunk_text)

        start += (CHUNK_SIZE - CHUNK_OVERLAP)

    return chunks