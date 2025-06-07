#!/usr/bin/env python3
"""
"""
T = TypeVar("T")

# Mapping of model names to tiktoken encoding names
MODEL_TO_ENCODING = {
    # OpenAI models
    "gpt-3.5-turbo": "cl100k_base",
    "gpt-4": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4o": "cl100k_base",
    "text-embedding-ada-002": "cl100k_base",
    # Anthropic models (using cl100k_base as approximation)
    "claude-instant-1": "cl100k_base",
    "claude-2": "cl100k_base",
    "claude-3-opus": "cl100k_base",
    "claude-3-sonnet": "cl100k_base",
    "claude-3-haiku": "cl100k_base",
    # Google models (using cl100k_base as approximation)
    "gemini-pro": "cl100k_base",
    "gemini-ultra": "cl100k_base",
    "text-embedding-gecko": "cl100k_base",
}

# Cache for encoders to avoid repeated initialization
_ENCODER_CACHE: Dict[str, Any] = {}

# Cache for token counts to avoid repeated computation
_TOKEN_COUNT_CACHE: Dict[str, int] = {}
_MAX_CACHE_SIZE = 10000

def get_encoding(model_name: str) -> Any:
    """
    """
        raise ValueError("tiktoken is not installed. Install with 'pip install tiktoken'")

    # Check cache first
    if model_name in _ENCODER_CACHE:
        return _ENCODER_CACHE[model_name]

    # Get encoding name for the model
    encoding_name = MODEL_TO_ENCODING.get(model_name)

    try:


        pass
        if encoding_name:
            # Get encoding by name
            encoding = tiktoken.get_encoding(encoding_name)
        else:
            # Try to get encoding directly for the model
            try:

                pass
                encoding = tiktoken.encoding_for_model(model_name)
            except Exception:

                pass
                # Fall back to cl100k_base for unknown models
                logger.warning(f"Unknown model: {model_name}, falling back to cl100k_base encoding")
                encoding = tiktoken.get_encoding("cl100k_base")

        # Cache the encoding
        _ENCODER_CACHE[model_name] = encoding
        return encoding

    except Exception:


        pass
        logger.error(f"Error getting encoding for model {model_name}: {e}")
        raise ValueError(f"Failed to get encoding for model {model_name}: {e}")

def _compute_hash(content: Any) -> str:
    """
    """
    return hashlib.md5(content_str.encode("utf-8")).hexdigest()

def _manage_cache_size() -> None:
    """Manage the token count cache size."""

def count_tokens(text: str, model_name: str = "gpt-4") -> int:
    """
    """
    cache_key = f"{model_name}:{_compute_hash(text)}"
    if cache_key in _TOKEN_COUNT_CACHE:
        return _TOKEN_COUNT_CACHE[cache_key]

    # Use tiktoken if available
    if HAS_TIKTOKEN:
        try:

            pass
            encoding = get_encoding(model_name)
            token_count = len(encoding.encode(text))

            # Cache the result
            _TOKEN_COUNT_CACHE[cache_key] = token_count
            _manage_cache_size()

            return token_count
        except Exception:

            pass
            logger.warning(f"Error counting tokens with tiktoken: {e}")
            # Fall back to heuristic method

    # Fallback heuristic method
    # 1. Count words (approx 0.75 tokens per word)
    # 2. Count special characters (approx 1 token per special char)
    # 3. Count whitespace (approx 0.25 tokens per whitespace)
    word_pattern = re.compile(r"\b\w+\b")
    special_char_pattern = re.compile(r"[^\w\s]")
    whitespace_pattern = re.compile(r"\s+")

    word_count = len(word_pattern.findall(text))
    special_char_count = len(special_char_pattern.findall(text))
    whitespace_count = len(whitespace_pattern.findall(text))

    # Calculate token estimate
    token_estimate = int(word_count * 0.75 + special_char_count + whitespace_count * 0.25 + 4)

    # Cache the result
    _TOKEN_COUNT_CACHE[cache_key] = token_estimate
    _manage_cache_size()

    return token_estimate

def count_tokens_recursive(content: Any, model_name: str = "gpt-4") -> int:
    """
    """
    cache_key = f"{model_name}:{_compute_hash(content)}"
    if cache_key in _TOKEN_COUNT_CACHE:
        return _TOKEN_COUNT_CACHE[cache_key]

    # Process based on content type
    if isinstance(content, str):
        token_count = count_tokens(content, model_name)
    elif isinstance(content, dict):
        # For dictionaries, count tokens for each key and value
        token_count = 0
        for key, value in content.items():
            token_count += count_tokens(str(key), model_name)
            token_count += count_tokens_recursive(value, model_name)
        # Add tokens for braces and commas
        token_count += 2 + max(0, len(content) - 1)
    elif isinstance(content, list):
        # For lists, count tokens for each item
        token_count = sum(count_tokens_recursive(item, model_name) for item in content)
        # Add tokens for brackets and commas
        token_count += 2 + max(0, len(content) - 1)
    else:
        # For other types, convert to string
        token_count = count_tokens(str(content), model_name)

    # Cache the result
    _TOKEN_COUNT_CACHE[cache_key] = token_count
    _manage_cache_size()

    return token_count

def estimate_memory_entry_tokens(entry: MemoryEntry, model_name: str = "gpt-4") -> int:
    """
    """
        cache_key = f"{model_name}:{entry.metadata.content_hash}"
        if cache_key in _TOKEN_COUNT_CACHE:
            return _TOKEN_COUNT_CACHE[cache_key]

    # Count tokens for the content
    token_count = count_tokens_recursive(entry.content, model_name)

    # Add tokens for metadata (simplified estimate)
    metadata_str = json.dumps(entry.metadata.to_dict())
    token_count += count_tokens(metadata_str, model_name)

    # Cache the result if content hash is available
    if entry.metadata.content_hash:
        cache_key = f"{model_name}:{entry.metadata.content_hash}"
        _TOKEN_COUNT_CACHE[cache_key] = token_count
        _manage_cache_size()

    return token_count

def with_token_counting(
    model_name: str = "gpt-4",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    """
                f"Token counts for {func.__name__}: args={args_tokens}, "
                f"kwargs={kwargs_tokens}, result={result_tokens}, "
                f"total={args_tokens + kwargs_tokens + result_tokens}",
                extra={
                    "token_count": {
                        "args": args_tokens,
                        "kwargs": kwargs_tokens,
                        "result": result_tokens,
                        "total": args_tokens + kwargs_tokens + result_tokens,
                    }
                },
            )

            return result

        return wrapper

    return decorator

class TokenEstimator:
    """Accurate token estimation for different LLM models."""
    def __init__(self, model_name: str = "gpt-4"):
        """
        """
        """
        """
        """
        """
        """Clear the token count cache."""
