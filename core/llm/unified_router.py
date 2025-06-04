"""
"""
    """Supported use cases for intelligent model selection"""
    CODE_GENERATION = "code_generation"
    ARCHITECTURE_DESIGN = "architecture_design"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    CHAT_CONVERSATION = "chat_conversation"
    MEMORY_PROCESSING = "memory_processing"
    WORKFLOW_COORDINATION = "workflow_coordination"
    DATA_ANALYSIS = "data_analysis"
    CREATIVE_WRITING = "creative_writing"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    GENERAL_PURPOSE = "general_purpose"

class ModelTier(str, Enum):
    """Model performance and cost tiers"""
    PREMIUM = "premium"      # Highest capability, highest cost
    STANDARD = "standard"    # Balanced performance and cost
    ECONOMY = "economy"      # Fast and economical
    SPECIALIZED = "specialized"  # Domain-specific models

class Provider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    PORTKEY = "portkey"
    OPENROUTER = "openrouter"
    AZURE = "azure"
    LITELLM = "litellm"

@dataclass
class ModelCapabilities:
    """Model capability metrics for intelligent selection"""
    """Complete model specification"""
    """Standard LLM request format"""
    """Standard LLM response format"""
    """Base exception for LLM operations"""
    """Rate limit exceeded error"""
    """Model temporarily unavailable"""
    """Configuration error"""
    """Abstract interface for LLM providers"""
        """Complete a chat request"""
        """Stream a chat completion"""
        """Generate embeddings"""
        """Get list of available models"""
        """Check provider health"""
    """OpenAI provider implementation"""
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )
        self._models = self._load_model_specs()
    
    def _load_model_specs(self) -> List[ModelSpec]:
        """Load OpenAI model specifications"""
                model_name="gpt-4-turbo",
                display_name="GPT-4 Turbo",
                tier=ModelTier.PREMIUM,
                capabilities=ModelCapabilities(
                    context_length=128000,
                    supports_tools=True,
                    supports_streaming=True,
                    supports_vision=True,
                    supports_code=True,
                    reasoning_quality=0.95,
                    speed_score=0.7,
                    cost_per_1k_tokens=0.03,
                    languages=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                ),
                use_cases=[UseCase.CODE_GENERATION, UseCase.ARCHITECTURE_DESIGN, 
                          UseCase.DEBUGGING, UseCase.GENERAL_PURPOSE],
                priority=90
            ),
            ModelSpec(
                provider=Provider.OPENAI,
                model_name="gpt-4o",
                display_name="GPT-4o",
                tier=ModelTier.STANDARD,
                capabilities=ModelCapabilities(
                    context_length=128000,
                    supports_tools=True,
                    supports_streaming=True,
                    supports_vision=True,
                    supports_code=True,
                    reasoning_quality=0.90,
                    speed_score=0.85,
                    cost_per_1k_tokens=0.015,
                    languages=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                ),
                use_cases=[UseCase.CHAT_CONVERSATION, UseCase.DOCUMENTATION, 
                          UseCase.SUMMARIZATION, UseCase.GENERAL_PURPOSE],
                priority=85
            ),
            ModelSpec(
                provider=Provider.OPENAI,
                model_name="gpt-3.5-turbo",
                display_name="GPT-3.5 Turbo",
                tier=ModelTier.ECONOMY,
                capabilities=ModelCapabilities(
                    context_length=16385,
                    supports_tools=True,
                    supports_streaming=True,
                    supports_vision=False,
                    supports_code=True,
                    reasoning_quality=0.75,
                    speed_score=0.95,
                    cost_per_1k_tokens=0.002,
                    languages=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                ),
                use_cases=[UseCase.CHAT_CONVERSATION, UseCase.SUMMARIZATION, 
                          UseCase.TRANSLATION, UseCase.GENERAL_PURPOSE],
                priority=70
            )
        ]
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Complete a chat request via OpenAI API"""
            "model": request.model or "gpt-4o",
            "messages": request.messages,
            "temperature": request.temperature or 0.7,
            "max_tokens": request.max_tokens or 2048,
            "stream": False
        }
        
        if request.tools:
            payload["tools"] = request.tools
        
        try:

        
            pass
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                provider=Provider.OPENAI,
                usage=data.get("usage", {}),
                cost=self._calculate_cost(data.get("usage", {}), payload["model"]),
                latency=time.time() - start_time,
                tool_calls=data["choices"][0]["message"].get("tool_calls")
            )
            
        except Exception:

            
            pass
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("retry-after", 60))
                raise RateLimitError(f"Rate limit exceeded: {e}", retry_after=retry_after, 
                                   provider=Provider.OPENAI, model=payload["model"])
            elif e.response.status_code >= 500:
                raise ModelUnavailableError(f"OpenAI service error: {e}", 
                                          provider=Provider.OPENAI, model=payload["model"])
            else:
                raise LLMError(f"OpenAI API error: {e}", provider=Provider.OPENAI, 
                             model=payload["model"], retryable=False)
    
    async def stream_complete(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream completion via OpenAI API"""
            "model": request.model or "gpt-4o",
            "messages": request.messages,
            "temperature": request.temperature or 0.7,
            "max_tokens": request.max_tokens or 2048,
            "stream": True
        }
        
        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    try:

                        pass
                        data = json.loads(chunk)
                        delta = data["choices"][0]["delta"]
                        if "content" in delta:
                            yield delta["content"]
                    except Exception:

                        pass
                        continue
    
    async def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Generate embeddings via OpenAI API"""
            "model": model or "text-embedding-3-small",
            "input": texts
        }
        
        response = await self.client.post("/embeddings", json=payload)
        response.raise_for_status()
        data = response.json()
        
        return [item["embedding"] for item in data["data"]]
    
    def get_available_models(self) -> List[ModelSpec]:
        """Get available OpenAI models"""
        """Check OpenAI API health"""
            response = await self.client.get("/models")
            return response.status_code == 200
        except Exception:

            pass
            return False
    
    def _calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate cost based on usage and model"""
        tokens = usage.get("total_tokens", 0)
        if "gpt-4-turbo" in model:
            return tokens * 0.03 / 1000
        elif "gpt-4o" in model:
            return tokens * 0.015 / 1000
        elif "gpt-3.5-turbo" in model:
            return tokens * 0.002 / 1000
        return 0.0

class AnthropicProvider(ProviderInterface):
    """Anthropic provider implementation"""
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            timeout=30.0
        )
        self._models = self._load_model_specs()
    
    def _load_model_specs(self) -> List[ModelSpec]:
        """Load Anthropic model specifications"""
                model_name="claude-3-opus-20240229",
                display_name="Claude 3 Opus",
                tier=ModelTier.PREMIUM,
                capabilities=ModelCapabilities(
                    context_length=200000,
                    supports_tools=True,
                    supports_streaming=True,
                    supports_vision=True,
                    supports_code=True,
                    reasoning_quality=0.98,
                    speed_score=0.6,
                    cost_per_1k_tokens=0.075,
                    languages=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                ),
                use_cases=[UseCase.CODE_GENERATION, UseCase.ARCHITECTURE_DESIGN, 
                          UseCase.DEBUGGING, UseCase.CREATIVE_WRITING],
                priority=95
            ),
            ModelSpec(
                provider=Provider.ANTHROPIC,
                model_name="claude-3-sonnet-20240229",
                display_name="Claude 3 Sonnet",
                tier=ModelTier.STANDARD,
                capabilities=ModelCapabilities(
                    context_length=200000,
                    supports_tools=True,
                    supports_streaming=True,
                    supports_vision=True,
                    supports_code=True,
                    reasoning_quality=0.92,
                    speed_score=0.8,
                    cost_per_1k_tokens=0.015,
                    languages=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                ),
                use_cases=[UseCase.CHAT_CONVERSATION, UseCase.DOCUMENTATION, 
                          UseCase.WORKFLOW_COORDINATION, UseCase.GENERAL_PURPOSE],
                priority=88
            ),
            ModelSpec(
                provider=Provider.ANTHROPIC,
                model_name="claude-3-haiku-20240307",
                display_name="Claude 3 Haiku",
                tier=ModelTier.ECONOMY,
                capabilities=ModelCapabilities(
                    context_length=200000,
                    supports_tools=True,
                    supports_streaming=True,
                    supports_vision=False,
                    supports_code=True,
                    reasoning_quality=0.85,
                    speed_score=0.95,
                    cost_per_1k_tokens=0.0025,
                    languages=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                ),
                use_cases=[UseCase.CHAT_CONVERSATION, UseCase.SUMMARIZATION, 
                          UseCase.MEMORY_PROCESSING, UseCase.GENERAL_PURPOSE],
                priority=75
            )
        ]
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Complete via Anthropic API"""
            "model": request.model or "claude-3-sonnet-20240229",
            "messages": messages,
            "max_tokens": request.max_tokens or 2048,
            "temperature": request.temperature or 0.7,
            "stream": False
        }
        
        if request.tools:
            payload["tools"] = self._convert_tools(request.tools)
        
        try:

        
            pass
            response = await self.client.post("/v1/messages", json=payload)
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["content"][0]["text"],
                model=data["model"],
                provider=Provider.ANTHROPIC,
                usage=data.get("usage", {}),
                cost=self._calculate_cost(data.get("usage", {}), payload["model"]),
                latency=time.time() - start_time
            )
            
        except Exception:

            
            pass
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded: {e}", 
                                   provider=Provider.ANTHROPIC, model=payload["model"])
            elif e.response.status_code >= 500:
                raise ModelUnavailableError(f"Anthropic service error: {e}", 
                                          provider=Provider.ANTHROPIC, model=payload["model"])
            else:
                raise LLMError(f"Anthropic API error: {e}", provider=Provider.ANTHROPIC, 
                             model=payload["model"], retryable=False)
    
    async def stream_complete(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream via Anthropic API"""
            "model": request.model or "claude-3-sonnet-20240229",
            "messages": messages,
            "max_tokens": request.max_tokens or 2048,
            "temperature": request.temperature or 0.7,
            "stream": True
        }
        
        async with self.client.stream("POST", "/v1/messages", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    try:

                        pass
                        data = json.loads(chunk)
                        if "delta" in data and "text" in data["delta"]:
                            yield data["delta"]["text"]
                    except Exception:

                        pass
                        continue
    
    async def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Anthropic doesn't provide embeddings - would need to use a different service"""
        raise NotImplementedError("Anthropic doesn't provide embedding models")
    
    def get_available_models(self) -> List[ModelSpec]:
        """Get available Anthropic models"""
        """Check Anthropic API health"""
        """Convert OpenAI message format to Anthropic format"""
            if msg.get("role") == "system":
                # Anthropic handles system messages differently
                # For now, we'll convert to user message
                converted.append({
                    "role": "user",
                    "content": f"System: {msg.get('content', '')}"
                })
            else:
                converted.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })
        return converted
    
    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI tools format to Anthropic format"""
        """Calculate cost based on usage and model"""
        tokens = usage.get("output_tokens", 0) + usage.get("input_tokens", 0)
        if "opus" in model:
            return tokens * 0.075 / 1000
        elif "sonnet" in model:
            return tokens * 0.015 / 1000
        elif "haiku" in model:
            return tokens * 0.0025 / 1000
        return 0.0

class IntelligentModelSelector:
    """Intelligent model selection based on use case and requirements"""
        """Select the best model for the given request"""
            raise ModelUnavailableError("No models available for any configured providers")
        
        # If specific model requested, find it
        if request.model:
            for model in candidate_models:
                if model.model_name == request.model:
                    return model
            logger.warning(f"Requested model {request.model} not found, selecting alternative")
        
        # Filter by tier
        tier_filtered = [model for model in candidate_models if model.tier == request.tier]
        if tier_filtered:
            candidate_models = tier_filtered
        
        # Filter by use case
        usecase_filtered = [
            model for model in candidate_models 
            if request.use_case in model.use_cases
        ]
        if usecase_filtered:
            candidate_models = usecase_filtered
        
        # Score and select best model
        best_model = max(candidate_models, key=lambda m: self._score_model(m, request))
        return best_model
    
    def _score_model(self, model: ModelSpec, request: LLMRequest) -> float:
        """Score a model based on request requirements"""
        model_key = f"{model.provider.value}:{model.model_name}"
        if model_key in self.performance_history:
            history = self.performance_history[model_key]
            score += history.get("success_rate", 0.5) * 20
            score -= history.get("avg_latency", 1.0) * 2
        
        return score
    
    def update_performance(self, model: str, provider: Provider, 
                          latency: float, success: bool) -> None:
        """Update performance history for a model"""
        model_key = f"{provider.value}:{model}"
        
        if model_key not in self.performance_history:
            self.performance_history[model_key] = {
                "total_requests": 0,
                "successful_requests": 0,
                "total_latency": 0.0,
                "success_rate": 0.0,
                "avg_latency": 0.0
            }
        
        history = self.performance_history[model_key]
        history["total_requests"] += 1
        if success:
            history["successful_requests"] += 1
        history["total_latency"] += latency
        
        # Update derived metrics
        history["success_rate"] = history["successful_requests"] / history["total_requests"]
        history["avg_latency"] = history["total_latency"] / history["total_requests"]

class UnifiedLLMRouter:
    """
    """
        """Initialize the unified router"""
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency": 0.0,
            "provider_usage": {},
            "model_usage": {},
            "error_counts": {}
        }
        
        # Initialize providers and model selector
        self._initialize_providers()
        self._initialize_model_selector()
    
    def _initialize_providers(self) -> None:
        """Initialize available providers based on configuration"""
                logger.info("OpenAI provider initialized")
            
            if anthropic_key:
                self.providers[Provider.ANTHROPIC] = AnthropicProvider(anthropic_key)
                logger.info("Anthropic provider initialized")
            
        except Exception:

            
            pass
            logger.warning(f"Provider initialization failed: {e}")
        
        # If no providers are available, log warning but don't fail
        if not self.providers:
            logger.warning("No LLM providers configured - router will work with mock responses")
    
    def _initialize_model_selector(self) -> None:
        """Initialize the intelligent model selector"""
        """Complete a request using the optimal model"""
            request = LLMRequest(messages=[{"role": "user", "content": request}])
        elif isinstance(request, list):
            request = LLMRequest(messages=request)
        
        # Check cache first
        cache_key = self._get_cache_key(request)
        if request.cache and cache_key in self.cache:
            cached_response, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_response
        
        # Handle case with no providers
        if not self.providers:
            logger.warning("No providers available - returning mock response")
            return LLMResponse(
                content="Mock response - no LLM providers configured",
                model="mock-model",
                provider=Provider.OPENAI,
                usage={"total_tokens": 10},
                cost=0.0,
                latency=0.1
            )
        
        # Select optimal model
        if not self.model_selector:
            self._initialize_model_selector()
        
        available_providers = list(self.providers.keys())
        selected_model = self.model_selector.select_model(request, available_providers)
        
        # Get provider for selected model
        provider = self.providers[selected_model.provider]
        
        # Update request with selected model
        request.model = selected_model.model_name
        
        # Execute request
        start_time = time.time()
        success = False
        response = None
        
        try:

        
            pass
            response = await self._attempt_completion(provider, request)
            success = True
            
            # Cache response
            if request.cache:
                self.cache[cache_key] = (response, time.time())
            
            # Update metrics
            self._update_metrics(response, success)
            
            # Update model performance
            latency = time.time() - start_time
            self.model_selector.update_performance(
                selected_model.model_name, 
                selected_model.provider, 
                latency, 
                success
            )
            
            return response
            
        except Exception:

            
            pass
            # Update metrics for failure
            self._update_metrics(None, success)
            
            # Update model performance
            latency = time.time() - start_time
            self.model_selector.update_performance(
                selected_model.model_name, 
                selected_model.provider, 
                latency, 
                success
            )
            
            logger.error(f"LLM request failed: {e}")
            raise
    
    async def stream_complete(self, request: Union[LLMRequest, str, List[Dict[str, str]]]) -> AsyncGenerator[str, None]:
        """Stream completion response"""
            request = LLMRequest(messages=[{"role": "user", "content": request}], stream=True)
        elif isinstance(request, list):
            request = LLMRequest(messages=request, stream=True)
        else:
            request.stream = True
        
        # Handle case with no providers
        if not self.providers:
            yield "Mock streaming response - no LLM providers configured"
            return
        
        # Select model and provider
        available_providers = list(self.providers.keys())
        selected_model = self.model_selector.select_model(request, available_providers)
        provider = self.providers[selected_model.provider]
        
        # Update request with selected model
        request.model = selected_model.model_name
        
        # Stream response
        async for chunk in provider.stream_complete(request):
            yield chunk
    
    async def embed(self, texts: Union[str, List[str]], model: Optional[str] = None) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text(s)"""
            raise ModelUnavailableError("No embedding provider available")
    
    async def _attempt_completion(self, provider: ProviderInterface, request: LLMRequest) -> LLMResponse:
        """Attempt completion with a specific provider"""
                    logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except Exception:

                
                pass
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Model unavailable, waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except Exception:

                
                pass
                if attempt < max_retries - 1:
                    logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(1)
                    continue
                raise
        
        raise LLMError("Max retries exceeded")
    
    def _get_cache_key(self, request: LLMRequest) -> str:
        """Generate cache key for request"""
            "messages": request.messages,
            "model": request.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "use_case": request.use_case.value,
            "tier": request.tier.value
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _update_metrics(self, response: Optional[LLMResponse], success: bool) -> None:
        """Update router metrics"""
        self.metrics["total_requests"] += 1
        
        if success and response:
            self.metrics["successful_requests"] += 1
            self.metrics["total_latency"] += response.latency
            
            # Update provider usage
            provider_key = response.provider.value
            self.metrics["provider_usage"][provider_key] = (
                self.metrics["provider_usage"].get(provider_key, 0) + 1
            )
            
            # Update model usage
            model_key = response.model
            self.metrics["model_usage"][model_key] = (
                self.metrics["model_usage"].get(model_key, 0) + 1
            )
        else:
            self.metrics["failed_requests"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get router performance metrics"""
        if self.metrics["total_requests"] > 0:
            success_rate = self.metrics["successful_requests"] / self.metrics["total_requests"]
        
        if self.metrics["successful_requests"] > 0:
            avg_latency = self.metrics["total_latency"] / self.metrics["successful_requests"]
        
        return {
            **self.metrics,
            "success_rate": success_rate,
            "avg_latency": avg_latency,
            "available_providers": list(self.providers.keys()),
            "cache_size": len(self.cache)
        }
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        """Perform health check on all providers"""
                logger.warning(f"Health check failed for {provider_name}: {e}")
                health_status[provider_name.value] = False
        
        return health_status
    
    async def close(self) -> None:
        """Clean up resources"""
    """Get or create the global router instance"""
    """Reset the global router instance"""
    """Convenience function for simple completion"""
        messages=[{"role": "user", "content": prompt}],
        use_case=use_case,
        tier=tier,
        **kwargs
    )
    response = await router.complete(request)
    return response.content

async def chat(messages: List[Dict[str, str]], **kwargs) -> str:
    """Convenience function for chat completion"""
    """Convenience function for streaming chat"""
    "UnifiedLLMRouter",
    "LLMRequest",
    "LLMResponse", 
    "UseCase",
    "ModelTier",
    "Provider",
    "LLMError",
    "RateLimitError",
    "ModelUnavailableError",
    "ConfigurationError",
    "get_llm_router",
    "reset_router",
    "complete",
    "chat",
    "stream_chat"
] 