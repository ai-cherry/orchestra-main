import time
import functools
import logging
import asyncio

def retry(max_attempts=3, delay=1, exponential_backoff=2):
    """
    Retry decorator for synchronous functions.
    Args:
        max_attempts (int): Total attempts (initial + retries).
        delay (float): Initial delay between attempts (seconds).
        exponential_backoff (float): Multiplier for delay after each failure.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.warning(
                        f"Attempt {attempt} failed for {func.__name__}: {e}"
                    )
                    if attempt == max_attempts:
                        logging.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )
                        raise
                    time.sleep(current_delay)
                    current_delay *= exponential_backoff
        return wrapper
    return decorator


def async_retry(max_attempts=3, delay=1, exponential_backoff=2):
    """
    Retry decorator for async functions.
    Args:
        max_attempts (int): Total attempts (initial + retries).
        delay (float): Initial delay between attempts (seconds).
        exponential_backoff (float): Multiplier for delay after each failure.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logging.warning(
                        f"[async] Attempt {attempt} failed for {func.__name__}: {e}"
                    )
                    if attempt == max_attempts:
                        logging.error(
                            f"[async] All {max_attempts} attempts failed for {func.__name__}"
                        )
                        raise
                    await asyncio.sleep(current_delay)
                    current_delay *= exponential_backoff
        return wrapper
    return decorator

# LLM model configuration
MODEL_ANTHROPIC_HAIKU = "anthropic/claude-3-haiku-20240307"
MODEL_OPENAI_GPT4 = "openai/gpt-4-turbo"

LLM_MODELS = {
    "simple": {
        "id": MODEL_ANTHROPIC_HAIKU,
        "temperature": 0.2,
        "max_tokens": 512,
    },
    "complex": {
        "id": MODEL_OPENAI_GPT4,
        "temperature": 0.7,
        "max_tokens": 2048,
    }
}

def get_llm_config(user_input, task_type_tag):
    word_count = len(user_input.split())
    if word_count < 50 and task_type_tag == "simple_query":
        return LLM_MODELS["simple"]
    return LLM_MODELS["complex"]

# Assignment/task registry
ASSIGNMENTS = {
    "summarize": "Summarize the following text as concisely as possible.",
    "generate_code": "Write Python code to solve the following problem.",
    # Add more as needed
}

def get_assignment_prompt(task_type_tag):
    return ASSIGNMENTS.get(task_type_tag) 