"""
Main module for the LLM Testing Server.

This server provides endpoints to test multiple LLM providers and analyze
their performance and reliability for the cascade setup.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

import prometheus_client as prom
import uvicorn
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Orchestra LLM Testing Service",
    description="Service for testing and benchmarking LLM providers",
)

# Provider clients - import and initialize lazily
provider_clients = {}

# Metrics
REQUEST_LATENCY = prom.Histogram(
    "llm_request_latency_seconds",
    "LLM request latency in seconds",
    ["provider", "model", "status"],
)
REQUEST_COUNT = prom.Counter(
    "llm_request_count", "Count of LLM requests", ["provider", "model", "status"]
)
TOKEN_COUNT = prom.Counter(
    "llm_token_count",
    "Count of tokens processed",
    ["provider", "model", "direction"],  # direction: input/output
)


# Request models
class TestRequest(BaseModel):
    """Request model for testing LLM providers."""

    prompt: str
    providers: List[str]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 500
    timeout: float = 15.0


class BenchmarkRequest(BaseModel):
    """Request for benchmarking multiple providers with the same prompt."""

    prompt: str
    runs: int = 5
    providers: List[str] = ["openrouter", "portkey", "openai", "anthropic", "deepseek"]
    models: Dict[str, str] = None  # Maps provider to model, optional


class CascadeTestRequest(BaseModel):
    """Request for testing the cascade failover setup."""

    prompt: str
    cascade_order: List[str] = [
        "openrouter",
        "portkey",
        "openai",
        "anthropic",
        "deepseek",
    ]
    inject_failures: List[str] = []  # List of providers to simulate failures for
    runs: int = 3


class ProviderResponse(BaseModel):
    """Response from a single LLM provider."""

    provider: str
    model: str
    content: str
    latency_ms: float
    status: str = "success"
    error: Optional[str] = None
    tokens: Optional[Dict[str, int]] = None


class TestResponse(BaseModel):
    """Response model for test endpoints."""

    results: List[ProviderResponse]
    timestamp: str
    cascade_used: Optional[bool] = None
    successful_providers: List[str]
    failed_providers: List[str]


# Provider initialization logic
def get_provider_client(provider_name: str):
    """Get or initialize a provider client."""
    global provider_clients

    if provider_name in provider_clients:
        return provider_clients[provider_name]

    # Initialize based on provider type
    try:
        if provider_name == "openrouter":
            import openrouter

            client = openrouter.OpenRouter(api_key=os.environ.get("OPENROUTER_API_KEY"))
            provider_clients[provider_name] = client
            return client

        elif provider_name == "portkey":
            import portkey

            client = portkey.Client(api_key=os.environ.get("PORTKEY_API_KEY"))
            provider_clients[provider_name] = client
            return client

        elif provider_name == "openai":
            import openai

            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            provider_clients[provider_name] = client
            return client

        elif provider_name == "anthropic":
            import anthropic

            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            provider_clients[provider_name] = client
            return client

        elif provider_name == "deepseek":
            import deepseek

            client = deepseek.Client(api_key=os.environ.get("DEEPSEEK_API_KEY"))
            provider_clients[provider_name] = client
            return client

        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

    except Exception as e:
        logger.error(f"Failed to initialize {provider_name}: {e}")
        raise ValueError(f"Failed to initialize {provider_name}: {e}")


async def call_provider(
    provider_name: str,
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 500,
    timeout: float = 15.0,
    inject_failure: bool = False,
) -> ProviderResponse:
    """Call an LLM provider and return the response."""
    # If we're injecting a failure, simulate it
    if inject_failure:
        await asyncio.sleep(0.5)  # Brief delay to simulate API call
        return ProviderResponse(
            provider=provider_name,
            model=model or "unknown",
            content="",
            latency_ms=500,
            status="error",
            error="Injected failure for testing",
        )

    # Start timing
    start_time = time.time()

    try:
        # Get the appropriate client
        client = get_provider_client(provider_name)

        # Set default model based on provider if not specified
        if not model:
            defaults = {
                "openrouter": "openai/gpt-3.5-turbo",
                "portkey": "openai/gpt-3.5-turbo",
                "openai": "gpt-3.5-turbo",
                "anthropic": "claude-instant-1",
                "deepseek": "deepseek-chat",
            }
            model = defaults.get(provider_name, "gpt-3.5-turbo")

        # Normalize model name for the specific provider
        provider_model = model
        if provider_name == "openrouter":
            if "/" not in provider_model:
                provider_model = f"openai/{provider_model}"
        elif provider_name == "openai":
            if "/" in provider_model:
                provider_model = provider_model.split("/")[-1]
        elif provider_name == "anthropic":
            if "/" in provider_model:
                provider_model = provider_model.split("/")[-1]
            if not provider_model.startswith("claude"):
                provider_model = "claude-instant-1"

        # Create messages format
        messages = [{"role": "user", "content": prompt}]

        # Call the appropriate API with timeout
        resp = None
        token_counts = {"input": 0, "output": 0}

        # Execute provider-specific call
        async def execute_call():
            nonlocal resp, token_counts

            if provider_name == "openrouter":
                completion = await client.chat.completions.create(
                    model=provider_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                resp = completion.choices[0].message.content
                token_counts = {
                    "input": completion.usage.prompt_tokens,
                    "output": completion.usage.completion_tokens,
                }

            elif provider_name == "portkey":
                completion = await client.chat.completions.create(
                    model=provider_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                resp = completion.choices[0].message.content
                token_counts = {
                    "input": completion.usage.prompt_tokens,
                    "output": completion.usage.completion_tokens,
                }

            elif provider_name == "openai":
                completion = await client.chat.completions.create(
                    model=provider_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                resp = completion.choices[0].message.content
                token_counts = {
                    "input": completion.usage.prompt_tokens,
                    "output": completion.usage.completion_tokens,
                }

            elif provider_name == "anthropic":
                completion = await client.messages.create(
                    model=provider_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                resp = completion.content[0].text
                token_counts = {
                    "input": completion.usage.input_tokens,
                    "output": completion.usage.output_tokens,
                }

            elif provider_name == "deepseek":
                # DeepSeek implementation depends on their client API
                completion = await client.chat.completions.create(
                    model=provider_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                resp = completion.choices[0].message.content
                token_counts = {
                    "input": completion.usage.prompt_tokens,
                    "output": completion.usage.completion_tokens,
                }

            else:
                raise ValueError(f"Unsupported provider: {provider_name}")

        # Execute with timeout
        try:
            await asyncio.wait_for(execute_call(), timeout=timeout)
        except asyncio.TimeoutError:
            elapsed_ms = (time.time() - start_time) * 1000
            REQUEST_COUNT.labels(
                provider=provider_name, model=model, status="timeout"
            ).inc()
            REQUEST_LATENCY.labels(
                provider=provider_name, model=model, status="timeout"
            ).observe(elapsed_ms / 1000)
            return ProviderResponse(
                provider=provider_name,
                model=provider_model,
                content="",
                latency_ms=elapsed_ms,
                status="timeout",
                error=f"Request timed out after {timeout} seconds",
            )

        # Calculate latency
        elapsed_ms = (time.time() - start_time) * 1000

        # Record metrics
        REQUEST_COUNT.labels(
            provider=provider_name, model=provider_model, status="success"
        ).inc()
        REQUEST_LATENCY.labels(
            provider=provider_name, model=provider_model, status="success"
        ).observe(elapsed_ms / 1000)

        if token_counts["input"] > 0:
            TOKEN_COUNT.labels(
                provider=provider_name, model=provider_model, direction="input"
            ).inc(token_counts["input"])
        if token_counts["output"] > 0:
            TOKEN_COUNT.labels(
                provider=provider_name, model=provider_model, direction="output"
            ).inc(token_counts["output"])

        # Return successful response
        return ProviderResponse(
            provider=provider_name,
            model=provider_model,
            content=resp,
            latency_ms=elapsed_ms,
            tokens=token_counts,
        )

    except Exception as e:
        # Calculate latency even for errors
        elapsed_ms = (time.time() - start_time) * 1000

        # Log and record error
        logger.error(f"Error calling {provider_name} with model {model}: {e}")
        REQUEST_COUNT.labels(
            provider=provider_name, model=model or "unknown", status="error"
        ).inc()
        REQUEST_LATENCY.labels(
            provider=provider_name, model=model or "unknown", status="error"
        ).observe(elapsed_ms / 1000)

        return ProviderResponse(
            provider=provider_name,
            model=model or "unknown",
            content="",
            latency_ms=elapsed_ms,
            status="error",
            error=str(e),
        )


async def cascade_call(
    prompt: str,
    cascade_order: List[str],
    inject_failures: List[str] = [],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 500,
    timeout: float = 10.0,
) -> ProviderResponse:
    """Attempt providers in sequence until a successful response."""
    for provider_name in cascade_order:
        inject_failure = provider_name in inject_failures
        response = await call_provider(
            provider_name=provider_name,
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            inject_failure=inject_failure,
        )

        # If successful, return this response
        if response.status == "success":
            return response

    # If we get here, all providers failed
    return ProviderResponse(
        provider="cascade",
        model="cascade",
        content="",
        latency_ms=0,
        status="error",
        error="All providers in cascade failed",
    )


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/test", response_model=TestResponse)
async def test_providers(request: TestRequest):
    """Test one or more LLM providers with the same prompt."""
    results = []
    successful = []
    failed = []

    # Call each provider
    for provider_name in request.providers:
        response = await call_provider(
            provider_name=provider_name,
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout=request.timeout,
        )

        results.append(response)

        if response.status == "success":
            successful.append(provider_name)
        else:
            failed.append(provider_name)

    return TestResponse(
        results=results,
        timestamp=datetime.now().isoformat(),
        successful_providers=successful,
        failed_providers=failed,
    )


@app.post("/benchmark", response_model=TestResponse)
async def benchmark_providers(
    request: BenchmarkRequest, background_tasks: BackgroundTasks
):
    """Benchmark multiple providers with the same prompt over multiple runs."""
    results = []
    successful = set()
    failed = set()

    # Prepare models mapping
    models = request.models or {}

    # Run benchmark
    for i in range(request.runs):
        for provider_name in request.providers:
            model = models.get(provider_name)

            response = await call_provider(
                provider_name=provider_name,
                prompt=request.prompt,
                model=model,
                temperature=0.7,
                max_tokens=500,
                timeout=15.0,
            )

            # Append run information
            response_dict = response.dict()
            response_dict["run"] = i + 1
            results.append(ProviderResponse(**response_dict))

            if response.status == "success":
                successful.add(provider_name)
            else:
                failed.add(provider_name)

    # Save results to file in background
    def save_results():
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"/app/monitoring/metrics/benchmark_{timestamp}.json"

            with open(filename, "w") as f:
                json.dump(
                    {
                        "prompt": request.prompt,
                        "runs": request.runs,
                        "results": [r.dict() for r in results],
                        "timestamp": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )
            logger.info(f"Benchmark results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save benchmark results: {e}")

    background_tasks.add_task(save_results)

    return TestResponse(
        results=results,
        timestamp=datetime.now().isoformat(),
        successful_providers=list(successful),
        failed_providers=list(failed),
    )


@app.post("/cascade", response_model=TestResponse)
async def test_cascade(request: CascadeTestRequest):
    """Test the cascade failover setup."""
    results = []
    successful_providers = []
    failed_providers = request.inject_failures.copy()

    for i in range(request.runs):
        response = await cascade_call(
            prompt=request.prompt,
            cascade_order=request.cascade_order,
            inject_failures=request.inject_failures,
            timeout=15.0,
        )

        results.append(response)

        if (
            response.status == "success"
            and response.provider not in successful_providers
        ):
            successful_providers.append(response.provider)

    return TestResponse(
        results=results,
        timestamp=datetime.now().isoformat(),
        cascade_used=True,
        successful_providers=successful_providers,
        failed_providers=failed_providers,
    )


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return prom.generate_latest()


# Define main function to run server
def start_server():
    """Start the LLM testing server."""
    uvicorn.run("llm_test_server.main:app", host="0.0.0.0", port=8001, log_level="info")


if __name__ == "__main__":
    start_server()
