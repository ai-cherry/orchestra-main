"""
"""
    """Supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    openai = "openai"

class ModelType(str, Enum):
    """Types of models."""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"

class LLMMessage(BaseModel):
    """A message for LLM interaction."""
    """Response from an LLM."""
    """Response from an embedding model."""
    """
    """
        """Initialize the LiteLLM client."""
            ModelProvider.OPENAI: api_key_openai or os.environ.get("OPENAI_API_KEY"),
            ModelProvider.ANTHROPIC: api_key_anthropic or os.environ.get("ANTHROPIC_API_KEY"),
            ModelProvider.GOOGLE: api_key_google or os.environ.get("GEMINI_API_KEY"),
            ModelProvider.AZURE_OPENAI: api_key_azure or os.environ.get("AZURE_OPENAI_API_KEY"),
        }

        # Set Azure API base
        self.api_base_azure = api_base_azure or os.environ.get("AZURE_OPENAI_API_BASE")

        # Set Vertex AI project and location
        self.vertex_project = vertex_project or settings.vultr_project_id
        self.vertex_location = vertex_location or settings.vultr_region

        # Set default models
        self.default_model = default_model or "gpt-3.5-turbo"
        self.default_embedding_model = default_embedding_model or "text-embedding-ada-002"

        # Configure LiteLLM
        self._configure_litellm()

    def _configure_litellm(self):
        """Configure LiteLLM with API keys and settings."""
                    os.environ["GOOGLE_API_KEY"] = api_key
                elif provider == ModelProvider.AZURE_OPENAI:
                    litellm.azure_api_key = api_key
                    if self.api_base_azure:
                        litellm.azure_api_base = self.api_base_azure

        # Configure Vertex AI if project and location are provided
        if self.vertex_project and self.vertex_location:
            os.environ["OPENAI_PROJECT"] = self.vertex_project
            os.environ["OPENAI_LOCATION"] = self.vertex_location

        # Set up logging
        litellm.set_verbose = True

    @retry(max_attempts=3, delay_seconds=1.0, backoff_factor=2.0)
    async def chat_completion(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        user: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> LLMResponse:
        """
        """
                "role": msg.role,
                "content": msg.content,
                **({"name": msg.name} if msg.name else {}),
            }
            for msg in messages
        ]

        try:


            pass
            response = await litellm.acompletion(
                model=model,
                messages=litellm_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop,
                user=user,
                timeout=timeout,
            )

            # Extract content from response
            content = response.choices[0].message.content

            # Extract usage information
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            return LLMResponse(
                model=model,
                content=content,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                raw_response=(response.model_dump() if hasattr(response, "model_dump") else response.dict()),
            )

        except Exception:


            pass
            logger.error(f"Error in chat completion: {str(e)}")
            raise

    @retry(max_attempts=3, delay_seconds=1.0, backoff_factor=2.0)
    async def text_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        user: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> LLMResponse:
        """
        """
        messages = [LLMMessage(role="user", content=prompt)]
        return await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop=stop,
            user=user,
            timeout=timeout,
        )

    @retry(max_attempts=3, delay_seconds=1.0, backoff_factor=2.0)
    async def get_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        user: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> LLMEmbeddingResponse:
        """
        """
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            return LLMEmbeddingResponse(
                model=model,
                embedding=embedding,
                usage=usage,
                raw_response=(response.model_dump() if hasattr(response, "model_dump") else response.dict()),
            )

        except Exception:


            pass
            logger.error(f"Error in embedding: {str(e)}")
            raise

    def get_available_models(self) -> Dict[ModelType, List[str]]:
        """
        """
                "gpt-3.5-turbo",
                "gpt-4",
                "gpt-4-turbo",
                "claude-3-opus",
                "claude-3-sonnet",
                "claude-3-haiku",
                "gemini-pro",
                "gemini-1.5-pro",
                "vertex-ai/gemini-pro",
                "vertex-ai/gemini-1.5-pro",
            ],
            ModelType.COMPLETION: [
                "gpt-3.5-turbo-instruct",
                "text-davinci-003",
            ],
            ModelType.EMBEDDING: [
                "text-embedding-ada-002",
                "text-embedding-3-small",
                "text-embedding-3-large",
                "vertex-ai/textembedding-gecko",
            ],
        }

    def get_token_limit(self, model: str) -> int:
        """
        """
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo": 128000,
            "claude-3-opus": 200000,
            "claude-3-sonnet": 180000,
            "claude-3-haiku": 150000,
            "gemini-pro": 32768,
            "gemini-1.5-pro": 1000000,
            "vertex-ai/gemini-pro": 32768,
            "vertex-ai/gemini-1.5-pro": 1000000,
            "text-embedding-ada-002": 8191,
            "text-embedding-3-small": 8191,
            "text-embedding-3-large": 8191,
        }

        return token_limits.get(model, 4096)  # Default to 4096 if model not found
