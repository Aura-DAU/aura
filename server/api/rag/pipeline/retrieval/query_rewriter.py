import os
import re
import time
from dotenv import load_dotenv
from groq import Groq, RateLimitError, APIStatusError, APIConnectionError

class QueryRewriter:

    def __init__(self):

        load_dotenv()
        from pipeline.key_manager import KeyManager
        self.KeyManager = KeyManager

        self.client = Groq(
            api_key=self.KeyManager.get_current_key()
        )

        self.model = os.getenv(
            "GROQ_MODEL",
            "qwen/qwen3-32b"
        )

    def rewrite(
        self,
        query,
        history=None
    ):

        if not history:
            return query

        history_text = ""

        for turn in history[-8:]:

            history_text += (
                f"{turn['role']}: "
                f"{turn['content']}\n"
            )

        prompt = f"""
Given the conversation history and the latest user question,
rewrite the latest question so it becomes fully self-contained.

Rules:
- Preserve the original meaning.
- Resolve references such as:
  he, she, him, her, they, them,
  this faculty member,
  this program,
  this event,
  it, its.
- Return ONLY the rewritten question.
- If the question is already self-contained, return it unchanged.

Conversation:

{history_text}

Latest Question:
{query}
"""

        max_retries = 15
        retry_delay = 5
        response = None
        keys_tried = set()

        attempt = 0
        while attempt < max_retries:
            try:
                self.client = Groq(api_key=self.KeyManager.get_current_key())
                response = (
                    self.client.chat.completions.create(
                        model=self.model,

                        temperature=0,

                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    )
                )
                break
            except (RateLimitError, APIStatusError, APIConnectionError) as e:
                status_code = getattr(e, "status_code", None)
                error_msg = str(e).lower()
                is_daily_limit = "tpd" in error_msg or "tokens per day" in error_msg or "rpd" in error_msg or "requests per day" in error_msg
                
                if is_daily_limit and status_code == 429:
                    current_key = self.KeyManager.get_current_key()
                    keys_tried.add(current_key)
                    if len(keys_tried) >= len(self.KeyManager._keys):
                        print("All API keys exhausted for daily limits in QueryRewriter. Failing request.")
                        raise e
                    
                    print(f"Daily rate limit hit in QueryRewriter: {e}. Rotating API key...")
                    self.KeyManager.rotate_key()
                    # Retry immediately with the new key without incrementing attempt or sleeping
                    continue
                
                is_retryable = (status_code in [429, 500, 502, 503, 504]) or isinstance(e, APIConnectionError)
                if is_retryable:
                    if attempt == max_retries - 1:
                        print("Max retries reached in QueryRewriter. Failing request.")
                        raise e
                    
                    retry_after = retry_delay
                    match = re.search(r"try again in (\d+(?:\.\d+)?)s", str(e))
                    if match:
                        retry_after = float(match.group(1)) + 1.0  # Add 1s buffer
                    
                    # Cap sleep at 65s since Groq token rate limits reset per minute
                    retry_after = min(retry_after, 65.0)
                    
                    print(f"API error/timeout {status_code} in QueryRewriter: {e}. Retrying in {retry_after:.2f} seconds...")
                    time.sleep(retry_after)
                    retry_delay *= 2
                    attempt += 1
                else:
                    raise e
            except Exception as e:
                raise e

        if not response:
            return query

        return (
            response
            .choices[0]
            .message
            .content
            .strip()
        )