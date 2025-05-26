"""
API middleware for response optimization in AI Orchestra.

This module provides middleware components for optimizing API responses,
including compression, caching, and payload optimization.
"""

import json
import time
import zlib
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
)

import brotli
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ...utils.logging import log_end, log_event, log_start


class CompressionAlgorithm(str, Enum):
    """Supported compression algorithms."""

    GZIP = "gzip"
    DEFLATE = "deflate"
    BROTLI = "br"
    NONE = "identity"


class ResponseCompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for compressing API responses.

    This middleware automatically compresses response payloads based on
    the client's Accept-Encoding header and payload size threshold.
    """

    def __init__(
        self,
        app: ASGIApp,
        min_size: int = 1024,  # Only compress responses larger than 1KB
        compression_level: int = 6,  # Balanced compression (1-9, higher = more compression)
        algorithm_preference: List[CompressionAlgorithm] = None,
        exclude_paths: Set[str] = None,
    ):
        """
        Initialize the compression middleware.

        Args:
            app: The ASGI application
            min_size: Minimum payload size for compression
            compression_level: Compression level (1-9)
            algorithm_preference: Ordered list of preferred compression algorithms
            exclude_paths: Set of URL paths to exclude from compression
        """
        super().__init__(app)
        self.min_size = min_size
        self.compression_level = compression_level
        self.algorithm_preference = algorithm_preference or [
            CompressionAlgorithm.BROTLI,  # Brotli offers best compression, but lowest compatibility
            CompressionAlgorithm.GZIP,  # GZIP is well-supported and good balance
            CompressionAlgorithm.DEFLATE,  # Deflate as a fallback
        ]
        self.exclude_paths = exclude_paths or set()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and compress the response.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The compressed response
        """
        # Skip compression for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Get the accepted encoding from the request
        accepted_encoding = request.headers.get("Accept-Encoding", "")

        # Find the best compression algorithm based on client support and our preference
        compression_algorithm = self._select_compression_algorithm(accepted_encoding)

        # If no compression is needed/supported, continue without compression
        if compression_algorithm == CompressionAlgorithm.NONE:
            return await call_next(request)

        # Get the original response
        response = await call_next(request)

        # Only compress if the response is not already compressed
        if "Content-Encoding" in response.headers:
            return response

        # Skip compression for streaming responses or small responses
        if (
            isinstance(response, StreamingResponse)
            or response.headers.get("Content-Length", "0").isdigit()
            and int(response.headers.get("Content-Length", "0")) < self.min_size
        ):
            return response

        # Get the response body
        body = b""
        if hasattr(response, "body"):
            body = response.body
        elif isinstance(response, StreamingResponse):
            # If it's a streaming response, we can't compress it directly
            return response

        # Skip if body is empty or too small
        if not body or len(body) < self.min_size:
            return response

        # Compress the body
        compressed_body = self._compress_body(body, compression_algorithm)

        # Skip compression if it didn't actually reduce the size
        if len(compressed_body) >= len(body):
            return response

        # Create a new response with the compressed body
        new_response = Response(
            content=compressed_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

        # Add compression headers
        new_response.headers["Content-Encoding"] = compression_algorithm.value
        new_response.headers["Content-Length"] = str(len(compressed_body))

        # Add Vary header to ensure proper caching
        new_response.headers["Vary"] = "Accept-Encoding"

        # Log compression metrics
        log_event(
            logger=None,
            category="compression",
            action="response_compressed",
            data={
                "path": request.url.path,
                "algorithm": compression_algorithm.value,
                "original_size": len(body),
                "compressed_size": len(compressed_body),
                "compression_ratio": round(len(compressed_body) / len(body) * 100, 2),
            },
        )

        return new_response

    def _select_compression_algorithm(
        self, accept_encoding: str
    ) -> CompressionAlgorithm:
        """
        Select the best compression algorithm based on client support.

        Args:
            accept_encoding: The Accept-Encoding header value

        Returns:
            The selected compression algorithm
        """
        # No compression if Accept-Encoding is empty
        if not accept_encoding:
            return CompressionAlgorithm.NONE

        # Parse the accepted encodings
        encodings = [e.strip() for e in accept_encoding.split(",")]

        # Try algorithms in our preferred order
        for algorithm in self.algorithm_preference:
            if algorithm.value in encodings:
                return algorithm

        # Default to no compression if no supported algorithm
        return CompressionAlgorithm.NONE

    def _compress_body(self, body: bytes, algorithm: CompressionAlgorithm) -> bytes:
        """
        Compress the response body.

        Args:
            body: The response body to compress
            algorithm: The compression algorithm to use

        Returns:
            The compressed body
        """
        if algorithm == CompressionAlgorithm.GZIP:
            compressor = zlib.compressobj(
                level=self.compression_level,
                method=zlib.DEFLATED,
                wbits=16 + zlib.MAX_WBITS,  # The 16 is for gzip
                memLevel=8,
                strategy=zlib.Z_DEFAULT_STRATEGY,
            )
            compressed_data = compressor.compress(body) + compressor.flush()
            return compressed_data

        elif algorithm == CompressionAlgorithm.DEFLATE:
            compressor = zlib.compressobj(
                level=self.compression_level,
                method=zlib.DEFLATED,
                wbits=-zlib.MAX_WBITS,  # Negative for raw deflate
                memLevel=8,
                strategy=zlib.Z_DEFAULT_STRATEGY,
            )
            compressed_data = compressor.compress(body) + compressor.flush()
            return compressed_data

        elif algorithm == CompressionAlgorithm.BROTLI:
            return brotli.compress(body, quality=self.compression_level)

        else:
            return body  # No compression


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding Cache-Control headers to responses.

    This middleware adds appropriate cache control headers based on the
    request path and method to improve client-side caching.
    """

    def __init__(
        self,
        app: ASGIApp,
        cache_config: Dict[str, Dict[str, Any]] = None,
    ):
        """
        Initialize the cache control middleware.

        Args:
            app: The ASGI application
            cache_config: Configuration for cache headers by path pattern
                {
                    "/static/*": {
                        "max_age": 86400,  # 1 day
                        "immutable": True,
                    },
                    "/api/v1/models": {
                        "max_age": 3600,  # 1 hour
                        "public": True,
                    }
                }
        """
        super().__init__(app)
        self.cache_config = cache_config or {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add cache headers to the response.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response with cache headers
        """
        # GET requests may be cacheable, others are typically not
        if request.method != "GET":
            response = await call_next(request)
            response.headers["Cache-Control"] = "no-store, max-age=0"
            return response

        # Process the request
        response = await call_next(request)

        # Don't modify cache headers if they're already set
        if "Cache-Control" in response.headers:
            return response

        # Find the matching cache config
        cache_directive = self._get_cache_directive(request.url.path)

        # Apply the cache directive
        if cache_directive:
            response.headers["Cache-Control"] = cache_directive
        else:
            # Default to no caching for API responses
            response.headers["Cache-Control"] = "no-cache, max-age=0"

        # Add Vary header for proper caching
        vary_headers = ["Accept", "Accept-Encoding"]
        if "Authorization" in request.headers:
            vary_headers.append("Authorization")

        response.headers["Vary"] = ", ".join(vary_headers)

        return response

    def _get_cache_directive(self, path: str) -> Optional[str]:
        """
        Get the cache directive for a path.

        Args:
            path: The request path

        Returns:
            Cache-Control header value, or None if no matching config
        """
        for pattern, config in self.cache_config.items():
            # Simple wildcard matching for now
            if pattern.endswith("*") and path.startswith(pattern[:-1]):
                return self._build_cache_control(config)
            elif pattern == path:
                return self._build_cache_control(config)

        return None

    def _build_cache_control(self, config: Dict[str, Any]) -> str:
        """
        Build a Cache-Control header from config.

        Args:
            config: The cache configuration

        Returns:
            Cache-Control header value
        """
        directives = []

        # Public or private
        if config.get("public", False):
            directives.append("public")
        else:
            directives.append("private")

        # Max age
        if "max_age" in config:
            directives.append(f"max-age={config['max_age']}")

        # S-maxage (for CDNs)
        if "s_maxage" in config:
            directives.append(f"s-maxage={config['s_maxage']}")

        # Other directives
        if config.get("immutable", False):
            directives.append("immutable")

        if config.get("no_transform", False):
            directives.append("no-transform")

        if config.get("must_revalidate", False):
            directives.append("must-revalidate")

        if config.get("proxy_revalidate", False):
            directives.append("proxy-revalidate")

        # Join all directives
        return ", ".join(directives)


class PayloadOptimizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for optimizing JSON payloads.

    This middleware implements field filtering based on query parameters
    to allow clients to request only specific fields, reducing payload size.
    """

    def __init__(
        self,
        app: ASGIApp,
        fields_param: str = "fields",
        max_fields: int = 100,
    ):
        """
        Initialize the payload optimization middleware.

        Args:
            app: The ASGI application
            fields_param: Query parameter for field filtering
            max_fields: Maximum number of fields to support
        """
        super().__init__(app)
        self.fields_param = fields_param
        self.max_fields = max_fields

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and optimize the response payload.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The optimized response
        """
        # Check if field filtering is requested
        fields = request.query_params.get(self.fields_param)
        if not fields:
            return await call_next(request)

        # Process requested fields
        requested_fields = set(fields.split(",")[: self.max_fields])
        if not requested_fields:
            return await call_next(request)

        # Process the original response
        response = await call_next(request)

        # Only process JSON responses
        if response.headers.get("content-type", "").startswith("application/json"):
            # Parse the response body
            if hasattr(response, "body"):
                try:
                    data = json.loads(response.body)
                    filtered_data = self._filter_json(data, requested_fields)

                    # Create a new response with the filtered data
                    return JSONResponse(
                        content=filtered_data,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                    )
                except json.JSONDecodeError:
                    # If the JSON is invalid, return the original response
                    pass

        return response

    def _filter_json(self, data: Any, fields: Set[str]) -> Any:
        """
        Filter JSON data to include only requested fields.

        Args:
            data: The JSON data to filter
            fields: Set of field names to include

        Returns:
            Filtered JSON data
        """
        if isinstance(data, dict):
            return {
                k: self._filter_json(v, fields) if k in fields else v
                for k, v in data.items()
                if k in fields
                or "." in next((f for f in fields if f.startswith(f"{k}.")), "")
            }
        elif isinstance(data, list):
            return [self._filter_json(item, fields) for item in data]
        else:
            return data


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking and logging response times.

    This middleware adds X-Response-Time headers and logs request timing
    for monitoring and performance analysis.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and track response time.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response with timing information
        """
        start_time = time.time()

        # Log start of request
        log_start(
            logger=None,
            action="request",
            data={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client": request.client.host if request.client else "unknown",
            },
        )

        # Process the request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Add timing header to response
        response.headers["X-Response-Time"] = f"{process_time:.6f}"

        # Log end of request
        log_end(
            logger=None,
            action="request",
            start_time=start_time,
            data={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time,
            },
        )

        return response


def add_performance_middlewares(
    app: FastAPI,
    compress_responses: bool = True,
    optimize_payloads: bool = True,
    add_cache_control: bool = True,
    track_response_time: bool = True,
    compression_config: Dict[str, Any] = None,
    cache_config: Dict[str, Dict[str, Any]] = None,
) -> None:
    """
    Add performance optimization middlewares to a FastAPI application.

    Args:
        app: The FastAPI application
        compress_responses: Whether to enable response compression
        optimize_payloads: Whether to enable payload optimization
        add_cache_control: Whether to add cache control headers
        track_response_time: Whether to track and log response times
        compression_config: Configuration for the compression middleware
        cache_config: Configuration for the cache control middleware
    """
    # Add middleware in reverse order (last added = first executed)

    # Response time tracking should be first to measure total time
    if track_response_time:
        app.add_middleware(ResponseTimeMiddleware)

    # Payload optimization should be before compression
    if optimize_payloads:
        app.add_middleware(
            PayloadOptimizationMiddleware,
            fields_param="fields",
            max_fields=100,
        )

    # Compression should be one of the last middlewares
    if compress_responses:
        compression_config = compression_config or {}
        app.add_middleware(
            ResponseCompressionMiddleware,
            min_size=compression_config.get("min_size", 1024),
            compression_level=compression_config.get("compression_level", 6),
            algorithm_preference=compression_config.get("algorithm_preference", None),
            exclude_paths=compression_config.get("exclude_paths", set()),
        )

    # Cache control should be after all content modifications
    if add_cache_control:
        app.add_middleware(
            CacheControlMiddleware,
            cache_config=cache_config
            or {
                "/static/*": {
                    "max_age": 86400,  # 1 day
                    "immutable": True,
                    "public": True,
                },
                "/api/models": {
                    "max_age": 3600,  # 1 hour
                    "public": True,
                },
                "/api/health": {
                    "max_age": 60,  # 1 minute
                    "public": True,
                },
            },
        )
