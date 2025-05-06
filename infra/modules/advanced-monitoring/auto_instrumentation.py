"""
Auto-instrumentation decorators for the Orchestra monitoring system.

This module provides decorators that automatically instrument functions and methods
to collect performance metrics, track errors, and report telemetry to Google Cloud Monitoring.
It integrates with the advanced monitoring system to enable auto-scaling and anomaly detection.
"""

import functools
import inspect
import logging
import os
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, cast

import google.cloud.monitoring_v3 as monitoring
from google.api_core import exceptions as google_exceptions
from google.cloud.monitoring_v3 import MetricServiceClient
from google.cloud.monitoring_v3.types import (
    MetricDescriptor,
    Point,
    TimeInterval,
    TimeSeries,
    TypedValue
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for decorator return types
F = TypeVar('F', bound=Callable[..., Any])

# Get project ID from environment variable
PROJECT_ID = os.environ.get("PROJECT_ID")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")

# Initialize metric client
_metric_client = None


def get_metric_client() -> MetricServiceClient:
    """Get or initialize the metric client."""
    global _metric_client
    if _metric_client is None:
        _metric_client = MetricServiceClient()
    return _metric_client


class MonitoredError(Exception):
    """
    Exception class for errors that are monitored.

    This can be used to track specific business-logic errors separately
    from general exceptions.
    """
    pass


def instrument(
    name: Optional[str] = None,
    track_args: bool = False,
    track_return_value: bool = False,
    error_threshold_ms: Optional[int] = None,
    labels: Optional[Dict[str, str]] = None
) -> Callable[[F], F]:
    """
    Decorator to instrument a function or method with metrics and tracing.

    Args:
        name: Custom name for the metric (defaults to function name)
        track_args: Whether to include argument values in telemetry
        track_return_value: Whether to include return values in telemetry
        error_threshold_ms: Threshold in ms above which to log execution as an error
        labels: Additional labels to add to the metrics

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        # Get function metadata
        func_name = name or func.__name__
        module_name = func.__module__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            error = None
            result = None

            # Process labels
            metric_labels = {
                "function": func_name,
                "module": module_name,
                "environment": ENVIRONMENT
            }
            if labels:
                metric_labels.update(labels)

            try:
                # Execute the function
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                # Re-raise the exception
                raise
            finally:
                # Calculate execution time
                execution_time_ms = (time.time() - start_time) * 1000

                # Determine if execution time exceeds threshold
                is_slow = error_threshold_ms is not None and execution_time_ms > error_threshold_ms

                # Report metrics
                try:
                    report_function_metrics(
                        func_name=func_name,
                        module_name=module_name,
                        execution_time_ms=execution_time_ms,
                        error=error is not None,
                        is_slow=is_slow,
                        labels=metric_labels
                    )

                    # Log additional details if enabled
                    if track_args and (error is not None or is_slow):
                        # Safely serialize args and kwargs
                        args_str = safely_serialize_args(args, kwargs)
                        logger.warning(
                            f"Function {func_name} issues: args={args_str}")

                    if track_return_value and error is None and is_slow:
                        # Safely serialize return value
                        result_str = safely_serialize_value(result)
                        logger.warning(
                            f"Slow function {func_name} returned: {result_str}")

                except Exception as metric_error:
                    # Don't let metrics reporting break functionality
                    logger.error(
                        f"Error reporting metrics for {func_name}: {metric_error}")

        return cast(F, wrapper)

    return decorator


def api_endpoint(
    name: Optional[str] = None,
    error_threshold_ms: int = 1000,  # 1 second
    track_request_body: bool = False
) -> Callable[[F], F]:
    """
    Specialized decorator for API endpoints that reports additional metrics.

    Args:
        name: Custom name for the endpoint
        error_threshold_ms: Threshold in ms above which to log execution as slow
        track_request_body: Whether to log request body on errors/slowness

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        endpoint_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            error = None
            response = None
            status_code = 200

            # Extract request if it's a FastAPI endpoint
            request = None
            request_info = {}

            # Look for request in args and kwargs
            for arg in args:
                if str(type(arg)).find("fastapi") >= 0 and str(type(arg)).find("Request") >= 0:
                    request = arg
                    break

            if request is None:
                for key, value in kwargs.items():
                    if key == "request" or (isinstance(value, object) and
                                            str(type(value)).find("fastapi") >= 0 and
                                            str(type(value)).find("Request") >= 0):
                        request = value
                        break

            # Extract request information if available
            if request is not None:
                try:
                    request_info = {
                        "method": getattr(request, "method", "UNKNOWN"),
                        "url": str(getattr(request, "url", "UNKNOWN")),
                        "client": getattr(request, "client", "UNKNOWN"),
                        "headers": dict(getattr(request, "headers", {}))
                    }

                    # Extract request body if needed
                    if track_request_body:
                        try:
                            body = await request.json() if hasattr(request, "json") else {}
                            # Sanitize sensitive information
                            if isinstance(body, dict):
                                for sensitive_key in ["password", "token", "key", "secret"]:
                                    if sensitive_key in body:
                                        body[sensitive_key] = "REDACTED"
                            request_info["body"] = body
                        except Exception:
                            request_info["body"] = "Could not parse body"

                except Exception as e:
                    logger.warning(f"Error extracting request info: {str(e)}")

            # Labels for metrics
            metric_labels = {
                "endpoint": endpoint_name,
                "method": request_info.get("method", "UNKNOWN"),
                "environment": ENVIRONMENT
            }

            try:
                # Execute the endpoint
                response = func(*args, **kwargs)

                # Handle async endpoints
                if inspect.isawaitable(response):
                    # We need to handle this differently since we can't use finally with await
                    return handle_async_response(
                        response, endpoint_name, start_time, error_threshold_ms,
                        metric_labels, request_info, track_request_body
                    )

                # Extract status code if response has it
                if hasattr(response, "status_code"):
                    status_code = response.status_code

                return response

            except Exception as e:
                error = e
                status_code = getattr(e, "status_code", 500)

                # Re-raise the exception
                raise

            finally:
                if not inspect.isawaitable(response):
                    # Calculate execution time
                    execution_time_ms = (time.time() - start_time) * 1000

                    # Determine if execution time exceeds threshold
                    is_slow = execution_time_ms > error_threshold_ms

                    # Add status code to labels
                    metric_labels["status_code"] = str(status_code)

                    # Report metrics
                    try:
                        report_api_metrics(
                            endpoint_name=endpoint_name,
                            execution_time_ms=execution_time_ms,
                            error=error is not None,
                            is_slow=is_slow,
                            status_code=status_code,
                            labels=metric_labels
                        )

                        # Log details for errors or slow requests
                        if (error is not None or is_slow) and track_request_body:
                            log_payload = {
                                "endpoint": endpoint_name,
                                "execution_time_ms": execution_time_ms,
                                "status_code": status_code,
                                "request_info": request_info,
                                "error": str(error) if error else None,
                                "is_slow": is_slow
                            }
                            logger.warning(
                                f"API issue detected: {log_payload}")

                    except Exception as metric_error:
                        # Don't let metrics reporting break functionality
                        logger.error(
                            f"Error reporting API metrics for {endpoint_name}: {metric_error}")

        return cast(F, wrapper)

    return decorator


async def handle_async_response(
    awaitable_response,
    endpoint_name: str,
    start_time: float,
    error_threshold_ms: int,
    metric_labels: Dict[str, str],
    request_info: Dict[str, Any],
    track_request_body: bool
):
    """
    Helper function to handle awaitable responses from async endpoints.
    """
    response = None
    error = None
    status_code = 200

    try:
        # Await the response
        response = await awaitable_response

        # Extract status code if response has it
        if hasattr(response, "status_code"):
            status_code = response.status_code

        return response

    except Exception as e:
        error = e
        status_code = getattr(e, "status_code", 500)
        raise

    finally:
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        # Determine if execution time exceeds threshold
        is_slow = execution_time_ms > error_threshold_ms

        # Add status code to labels
        metric_labels["status_code"] = str(status_code)

        # Report metrics
        try:
            report_api_metrics(
                endpoint_name=endpoint_name,
                execution_time_ms=execution_time_ms,
                error=error is not None,
                is_slow=is_slow,
                status_code=status_code,
                labels=metric_labels
            )

            # Log details for errors or slow requests
            if (error is not None or is_slow) and track_request_body:
                log_payload = {
                    "endpoint": endpoint_name,
                    "execution_time_ms": execution_time_ms,
                    "status_code": status_code,
                    "request_info": request_info,
                    "error": str(error) if error else None,
                    "is_slow": is_slow
                }
                logger.warning(f"API issue detected: {log_payload}")

        except Exception as metric_error:
            # Don't let metrics reporting break functionality
            logger.error(
                f"Error reporting API metrics for {endpoint_name}: {metric_error}")


def llm_call(
    provider: str = "generic",
    track_prompt: bool = False,
    track_response: bool = False,
    error_threshold_ms: int = 5000  # 5 seconds
) -> Callable[[F], F]:
    """
    Specialized decorator for LLM API calls that reports additional metrics.

    Args:
        provider: LLM provider name (e.g., "openai", "anthropic", "vertex")
        track_prompt: Whether to log prompt on errors
        track_response: Whether to log response on errors
        error_threshold_ms: Threshold in ms above which to log execution as slow

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        func_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            error = None
            token_count = 0
            model = "unknown"

            # Try to extract model information
            for key, value in kwargs.items():
                if key in ["model", "model_name", "model_id"] and isinstance(value, str):
                    model = value
                    break

            # Create metric labels
            metric_labels = {
                "function": func_name,
                "provider": provider,
                "model": model,
                "environment": ENVIRONMENT
            }

            # Extract prompt for potential logging
            prompt = None
            if track_prompt:
                for key, value in kwargs.items():
                    if key in ["prompt", "messages", "input", "text"]:
                        prompt = value
                        break

                if prompt is None and len(args) > 0:
                    # Assume first positional arg might be the prompt
                    prompt = args[0]

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Handle async LLM calls
                if inspect.isawaitable(result):
                    return handle_async_llm_call(
                        result, func_name, provider, model, start_time,
                        error_threshold_ms, metric_labels, prompt, track_prompt, track_response
                    )

                # Try to extract token count if available
                if result and isinstance(result, dict):
                    if "usage" in result and isinstance(result["usage"], dict):
                        token_count = result["usage"].get("total_tokens", 0)
                    elif "tokenCount" in result:
                        token_count = result.get("tokenCount", 0)

                return result

            except Exception as e:
                error = e
                # Re-raise the exception
                raise

            finally:
                if not inspect.isawaitable(result):
                    # Calculate execution time
                    execution_time_ms = (time.time() - start_time) * 1000

                    # Report metrics
                    try:
                        report_llm_metrics(
                            function_name=func_name,
                            provider=provider,
                            model=model,
                            execution_time_ms=execution_time_ms,
                            error=error is not None,
                            token_count=token_count,
                            labels=metric_labels
                        )

                        # Log details for errors or slow requests
                        is_slow = execution_time_ms > error_threshold_ms
                        if error is not None or is_slow:
                            log_data = {
                                "function": func_name,
                                "provider": provider,
                                "model": model,
                                "execution_time_ms": execution_time_ms,
                                "error": str(error) if error else None,
                                "is_slow": is_slow,
                                "token_count": token_count
                            }

                            # Add prompt if tracking
                            if track_prompt and prompt is not None:
                                log_data["prompt"] = safely_serialize_value(
                                    prompt)

                            # Add response if tracking and available
                            if track_response and not error and hasattr(result, "__dict__"):
                                log_data["response"] = safely_serialize_value(
                                    result)

                            logger.warning(f"LLM call issue: {log_data}")

                    except Exception as metric_error:
                        # Don't let metrics reporting break functionality
                        logger.error(
                            f"Error reporting LLM metrics for {func_name}: {metric_error}")

        return cast(F, wrapper)

    return decorator


async def handle_async_llm_call(
    awaitable_result,
    function_name: str,
    provider: str,
    model: str,
    start_time: float,
    error_threshold_ms: int,
    metric_labels: Dict[str, str],
    prompt: Any,
    track_prompt: bool,
    track_response: bool
):
    """
    Helper function to handle awaitable results from async LLM calls.
    """
    error = None
    token_count = 0

    try:
        # Await the result
        result = await awaitable_result

        # Try to extract token count if available
        if result and isinstance(result, dict):
            if "usage" in result and isinstance(result["usage"], dict):
                token_count = result["usage"].get("total_tokens", 0)
            elif "tokenCount" in result:
                token_count = result.get("tokenCount", 0)

        return result

    except Exception as e:
        error = e
        raise

    finally:
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        # Report metrics
        try:
            report_llm_metrics(
                function_name=function_name,
                provider=provider,
                model=model,
                execution_time_ms=execution_time_ms,
                error=error is not None,
                token_count=token_count,
                labels=metric_labels
            )

            # Log details for errors or slow requests
            is_slow = execution_time_ms > error_threshold_ms
            if error is not None or is_slow:
                log_data = {
                    "function": function_name,
                    "provider": provider,
                    "model": model,
                    "execution_time_ms": execution_time_ms,
                    "error": str(error) if error else None,
                    "is_slow": is_slow,
                    "token_count": token_count
                }

                # Add prompt if tracking
                if track_prompt and prompt is not None:
                    log_data["prompt"] = safely_serialize_value(prompt)

                # Add response if tracking and available
                if track_response and not error and result:
                    log_data["response"] = safely_serialize_value(result)

                logger.warning(f"LLM call issue: {log_data}")

        except Exception as metric_error:
            # Don't let metrics reporting break functionality
            logger.error(
                f"Error reporting LLM metrics for {function_name}: {metric_error}")


def database_operation(
    database_type: str = "generic",
    operation_type: Optional[str] = None,
    error_threshold_ms: int = 1000,  # 1 second
    collection: Optional[str] = None
) -> Callable[[F], F]:
    """
    Specialized decorator for database operations.

    Args:
        database_type: Type of database (e.g., "postgres", "mongo", "redis")
        operation_type: Type of operation (e.g., "read", "write", "query")
        error_threshold_ms: Threshold in ms above which to log execution as slow
        collection: Optional collection or table name

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        func_name = func.__name__

        # Infer operation type from function name if not provided
        inferred_operation = operation_type
        if not inferred_operation:
            if any(op in func_name.lower() for op in ["get", "find", "select", "query", "fetch"]):
                inferred_operation = "read"
            elif any(op in func_name.lower() for op in ["save", "insert", "update", "create", "set"]):
                inferred_operation = "write"
            elif any(op in func_name.lower() for op in ["delete", "remove", "drop"]):
                inferred_operation = "delete"
            else:
                inferred_operation = "query"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            error = None

            # Labels for metrics
            metric_labels = {
                "function": func_name,
                "database_type": database_type,
                "operation_type": inferred_operation,
                "environment": ENVIRONMENT
            }

            # Add collection if provided
            if collection:
                metric_labels["collection"] = collection

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Handle async database operations
                if inspect.isawaitable(result):
                    return handle_async_db_operation(
                        result, func_name, database_type, inferred_operation,
                        start_time, error_threshold_ms, metric_labels
                    )

                return result

            except Exception as e:
                error = e
                # Re-raise the exception
                raise

            finally:
                if not inspect.isawaitable(result):
                    # Calculate execution time
                    execution_time_ms = (time.time() - start_time) * 1000

                    # Determine if execution time exceeds threshold
                    is_slow = execution_time_ms > error_threshold_ms

                    # Report metrics
                    try:
                        report_database_metrics(
                            function_name=func_name,
                            database_type=database_type,
                            operation_type=inferred_operation,
                            execution_time_ms=execution_time_ms,
                            error=error is not None,
                            is_slow=is_slow,
                            labels=metric_labels
                        )

                        # Log details for errors or slow operations
                        if error is not None or is_slow:
                            log_data = {
                                "function": func_name,
                                "database_type": database_type,
                                "operation_type": inferred_operation,
                                "execution_time_ms": execution_time_ms,
                                "error": str(error) if error else None,
                                "is_slow": is_slow
                            }
                            if collection:
                                log_data["collection"] = collection

                            logger.warning(
                                f"Database operation issue: {log_data}")

                    except Exception as metric_error:
                        # Don't let metrics reporting break functionality
                        logger.error(
                            f"Error reporting database metrics for {func_name}: {metric_error}")

        return cast(F, wrapper)

    return decorator


async def handle_async_db_operation(
    awaitable_result,
    function_name: str,
    database_type: str,
    operation_type: str,
    start_time: float,
    error_threshold_ms: int,
    metric_labels: Dict[str, str]
):
    """
    Helper function to handle awaitable results from async database operations.
    """
    error = None

    try:
        # Await the result
        result = await awaitable_result
        return result

    except Exception as e:
        error = e
        raise

    finally:
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        # Determine if execution time exceeds threshold
        is_slow = execution_time_ms > error_threshold_ms

        # Report metrics
        try:
            report_database_metrics(
                function_name=function_name,
                database_type=database_type,
                operation_type=operation_type,
                execution_time_ms=execution_time_ms,
                error=error is not None,
                is_slow=is_slow,
                labels=metric_labels
            )

            # Log details for errors or slow operations
            if error is not None or is_slow:
                log_data = {
                    "function": function_name,
                    "database_type": database_type,
                    "operation_type": operation_type,
                    "execution_time_ms": execution_time_ms,
                    "error": str(error) if error else None,
                    "is_slow": is_slow
                }

                if "collection" in metric_labels:
                    log_data["collection"] = metric_labels["collection"]

                logger.warning(f"Database operation issue: {log_data}")

        except Exception as metric_error:
            # Don't let metrics reporting break functionality
            logger.error(
                f"Error reporting database metrics for {function_name}: {metric_error}")


# Helper functions for metric reporting

def report_function_metrics(
    func_name: str,
    module_name: str,
    execution_time_ms: float,
    error: bool,
    is_slow: bool,
    labels: Dict[str, str]
) -> None:
    """Report metrics for a function call."""
    if not PROJECT_ID:
        logger.warning(
            "PROJECT_ID environment variable not set, skipping metrics")
        return

    try:
        client = get_metric_client()

        # Create time series for execution time
        create_time_series(
            client=client,
            metric_type="custom.googleapis.com/orchestra/function/execution_time",
            metric_kind=MetricDescriptor.MetricKind.GAUGE,
            value_type=MetricDescriptor.ValueType.DOUBLE,
            value=execution_time_ms,
            labels=labels
        )

        # Create time series for errors (as a count)
        if error:
            create_time_series(
                client=client,
                metric_type="custom.googleapis.com/orchestra/function/errors",
                metric_kind=MetricDescriptor.MetricKind.CUMULATIVE,
                value_type=MetricDescriptor.ValueType.INT64,
                value=1,
                labels=labels
            )

        # Create time series for slow executions (as a count)
        if is_slow:
            create_time_series(
                client=client,
                metric_type="custom.googleapis.com/orchestra/function/slow_execution",
                metric_kind=MetricDescriptor.MetricKind.CUMULATIVE,
                value_type=MetricDescriptor.ValueType.INT64,
                value=1,
                labels=labels
            )

    except Exception as e:
        logger.error(f"Error reporting function metrics: {str(e)}")


def report_api_metrics(
    endpoint_name: str,
    execution_time_ms: float,
    error: bool,
    is_slow: bool,
    status_code: int,
    labels: Dict[str, str]
) -> None:
    """Report metrics for an API endpoint call."""
    if not PROJECT_ID:
        logger.warning(
            "PROJECT_ID environment variable not set, skipping metrics")
        return

    try:
        client = get_metric_client()

        # Create time series for execution time
        create_time_series(
            client=client,
            metric_type="custom.googleapis.com/orchestra/api/latency",
            metric_kind=MetricDescriptor.MetricKind.GAUGE,
            value_type=MetricDescriptor.ValueType.DOUBLE,
            value=execution_time_ms,
            labels=labels
        )

        # Create time series for request count
        create_time_series(
            client=client,
            metric_type="custom.googleapis.com/orchestra/api/requests",
            metric_kind=MetricDescriptor.MetricKind.CUMULATIVE,
            value_type=MetricDescriptor.ValueType.INT64,
            value=1,
            labels=labels
        )

        # Create time series for errors (if applicable)
        if error or status_code >= 400:
            error_labels = labels.copy()
            error_labels["status_code"] = str(status_code)

            create_time_series(
                client=client,
                metric_type="custom.googleapis.com/orchestra/api/errors",
                metric_kind=MetricDescriptor.MetricKind.CUMULATIVE,
                value_type=MetricDescriptor.ValueType.INT64,
                value=1,
                labels=error_labels
            )

    except Exception as e:
        logger.error(f"Error reporting API metrics: {str(e)}")


def report_llm_metrics(
    function_name: str,
    provider: str,
    model: str,
    execution_time_ms: float,
    error: bool,
    token_count: int,
    labels: Dict[str, str]
) -> None:
    """Report metrics for an LLM API call."""
    if not PROJECT_ID:
        logger.warning(
            "PROJECT_ID environment variable not set, skipping metrics")
        return

    try:
        client = get_metric_client()

        # Create time series for execution time
        create_time_series(
            client=client,
            metric_type="custom.googleapis.com/orchestra/llm/latency",
            metric_kind=MetricDescriptor.MetricKind.GAUGE,
            value_type=MetricDescriptor.ValueType.DOUBLE,
            value=execution_time_ms,
            labels=labels
        )

        # Create time series for token count
        if token_count > 0:
            create_time_series(
                client=client,
                metric_type="custom.googleapis.com/orchestra/llm/tokens",
                metric_kind=MetricDescriptor.MetricKind.GAUGE,
                value_type=MetricDescriptor.ValueType.INT64,
                value=token_count,
                labels=labels
            )

        # Create time series for request count
        create_time_series(
            client=client,
            metric_type="custom.googleapis.com/orchestra/llm/requests",
            metric_kind=MetricDescriptor.MetricKind.CUMULATIVE,
            value_type=MetricDescriptor.ValueType.INT64,
            value=1,
            labels=labels
        )

        # Create time series for errors (if applicable)
        if error:
            create_time_series(
                client=client,
                metric_type="custom.googleapis.com/orchestra/llm/errors",
                metric_kind=MetricDescriptor.MetricKind.CUMULATIVE,
                value_type=MetricDescriptor.ValueType.INT64,
                value=1,
                labels=labels
            )

    except Exception as e:
        logger.error(f"Error reporting LLM metrics: {str(e)}")


def report_database_metrics(
    function_name: str,
    database_type: str,
    operation_type: str,
    execution_time_ms: float,
    error: bool,
    is_slow: bool,
    labels: Dict[str, str]
) -> None:
    """Report metrics for a database operation."""
    if not PROJECT_ID:
        logger.warning(
            "PROJECT_ID environment variable not set, skipping metrics")
        return

    try:
        client = get_metric_client()

        # Create time series for execution time
        create_time_series(
            client=client,
            metric_type="custom.googleapis.com/orchestra/database/latency",
            metric_kind=MetricDescriptor.MetricKind.GAUGE,
            value_type=MetricDescriptor.ValueType.DOUBLE,
            value=execution_time_ms,
            labels=labels
        )

        # Create time series for operation count
        create_time_series(
            client=client,
            metric_type="custom.googleapis.com/orchestra/database/operations",
            metric_kind=MetricDescriptor.MetricKind.CUMULATIVE,
            value_type=MetricDescriptor.ValueType.INT64,
            value=1,
            labels=labels
        )

        # Create time series for errors (if applicable)
        if error:
            create_time_series(
                client=client,
                metric_type="custom.googleapis.com/orchestra/database/errors",
                metric_kind=MetricDescriptor.MetricKind.CUMULATIVE,
                value_type=MetricDescriptor.ValueType.INT64,
                value=1,
                labels=labels
            )

        # Create time series for slow operations (if applicable)
        if is_slow:
            create_time_series(
                client=client,
                metric_type="custom.googleapis.com/orchestra/database/slow_operations",
                metric_kind=MetricDescriptor.MetricKind.CUMULATIVE,
                value_type=MetricDescriptor.ValueType.INT64,
                value=1,
                labels=labels
            )

    except Exception as e:
        logger.error(f"Error reporting database metrics: {str(e)}")


def create_time_series(
    client: MetricServiceClient,
    metric_type: str,
    metric_kind: MetricDescriptor.MetricKind,
    value_type: MetricDescriptor.ValueType,
    value: float,
    labels: Dict[str, str]
) -> None:
    """
    Create and write a time series for a metric.

    Args:
        client: The metric client
        metric_type: The name of the metric
        metric_kind: The kind of metric (GAUGE, CUMULATIVE, etc.)
        value_type: The type of the value (DOUBLE, INT64, etc.)
        value: The value to record
        labels: Labels to attach to the metric
    """
    project_name = f"projects/{PROJECT_ID}"

    # Create the specific metric object
    metric = {
        "type": metric_type,
        "labels": labels
    }

    # Create the resource object
    resource = {
        "type": "global",
        "labels": {
            "project_id": PROJECT_ID
        }
    }

    # Create the time series
    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10**9)

    # Create the interval
    interval = TimeInterval()
    interval.end_time.seconds = seconds
    interval.end_time.nanos = nanos

    # For cumulative metrics, set start time to 1 hour ago
    if metric_kind == MetricDescriptor.MetricKind.CUMULATIVE:
        interval.start_time.seconds = seconds - 3600
        interval.start_time.nanos = nanos

    # Create the point
    point = Point()
    point.interval = interval

    # Set the value based on type
    if value_type == MetricDescriptor.ValueType.DOUBLE:
        point.value.double_value = value
    elif value_type == MetricDescriptor.ValueType.INT64:
        point.value.int64_value = int(value)
    else:
        raise ValueError(f"Unsupported value type: {value_type}")

    # Create the time series request
    series = TimeSeries()
    series.metric = metric
    series.resource = resource
    series.points = [point]

    # Write the time series
    client.create_time_series(
        name=project_name,
        time_series=[series]
    )


# Utility functions

def safely_serialize_args(args: tuple, kwargs: dict) -> str:
    """
    Safely convert function arguments to string for logging.
    Handles large objects and sensitive information.
    """
    try:
        # Truncate and sanitize args
        safe_args = []
        for arg in args:
            safe_args.append(safely_serialize_value(arg))

        # Truncate and sanitize kwargs
        safe_kwargs = {}
        for key, value in kwargs.items():
            # Skip or redact sensitive keys
            if key.lower() in ["password", "token", "key", "secret", "credential"]:
                safe_kwargs[key] = "REDACTED"
            else:
                safe_kwargs[key] = safely_serialize_value(value)

        return f"args={safe_args}, kwargs={safe_kwargs}"
    except Exception:
        return "Failed to serialize arguments"


def safely_serialize_value(value: Any) -> Any:
    """
    Safely convert a value to a serializable format for logging.
    Handles large objects and sensitive information.
    """
    try:
        if isinstance(value, (str, int, float, bool, type(None))):
            # For simple types, return as is (with truncation for strings)
            if isinstance(value, str) and len(value) > 500:
                return value[:497] + "..."
            return value

        elif isinstance(value, (list, tuple)):
            # For lists/tuples, process each item
            if len(value) > 10:
                # For large lists, truncate
                return [safely_serialize_value(item) for item in value[:10]] + ["..."]
            return [safely_serialize_value(item) for item in value]

        elif isinstance(value, dict):
            # For dictionaries, process each key/value
            if len(value) > 10:
                # For large dicts, truncate
                result = {}
                for i, (k, v) in enumerate(value.items()):
                    if i >= 10:
                        result["..."] = "..."
                        break
                    # Skip or redact sensitive keys
                    if isinstance(k, str) and k.lower() in ["password", "token", "key", "secret", "credential"]:
                        result[k] = "REDACTED"
                    else:
                        result[k] = safely_serialize_value(v)
                return result

            result = {}
            for k, v in value.items():
                # Skip or redact sensitive keys
                if isinstance(k, str) and k.lower() in ["password", "token", "key", "secret", "credential"]:
                    result[k] = "REDACTED"
                else:
                    result[k] = safely_serialize_value(v)
            return result

        elif hasattr(value, "__dict__"):
            # For objects, convert to dict representation
            return safely_serialize_value(vars(value))

        else:
            # For other types, use string representation
            return str(value)
    except Exception:
        return "Unserializable value"
