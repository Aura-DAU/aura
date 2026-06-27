import re
from transformers import AutoTokenizer
from config import (MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def split_section(text):
    """
    Split section into semantic sentence-boundary chunks with overlap.
    """
    # Split text into sentences using regex
    # Lookbehinds ensure we do not split on common abbreviations or initials
    sentence_end = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s')
    sentences = sentence_end.split(text)
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        sentence_tokens = len(tokenizer.encode(sentence, add_special_tokens=False))
        
        # If a single sentence exceeds the CHUNK_SIZE, split it by tokens
        if sentence_tokens > CHUNK_SIZE:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_tokens = 0
            
            tokens = tokenizer.encode(sentence, add_special_tokens=False)
            start = 0
            while start < len(tokens):
                end = start + CHUNK_SIZE
                chunk_text = tokenizer.decode(tokens[start:end], skip_special_tokens=True)
                chunks.append(chunk_text)
                start += (CHUNK_SIZE - CHUNK_OVERLAP)
            continue
            
        if current_tokens + sentence_tokens > CHUNK_SIZE:
            chunks.append(" ".join(current_chunk))
            
            # Find the overlap sentence-by-sentence to remain within CHUNK_OVERLAP tokens
            overlap_chunk = []
            overlap_tokens = 0
            for s in reversed(current_chunk):
                s_tokens = len(tokenizer.encode(s, add_special_tokens=False))
                if overlap_tokens + s_tokens <= CHUNK_OVERLAP:
                    overlap_chunk.insert(0, s)
                    overlap_tokens += s_tokens
                else:
                    break
            current_chunk = overlap_chunk
            current_tokens = overlap_tokens
            
        current_chunk.append(sentence)
        current_tokens += sentence_tokens
        
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks