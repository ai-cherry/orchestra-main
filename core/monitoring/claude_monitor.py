# TODO: Consider adding connection pooling configuration
"""
"""
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240229": {"input": 0.25, "output": 1.25},
    "claude-4-20250522": {"input": 20.00, "output": 100.00},  # Placeholder pricing
    "claude-4-opus-20250522": {"input": 25.00, "output": 125.00},
    "claude-4-sonnet-20250522": {"input": 5.00, "output": 25.00},
}

@dataclass
class APICallMetrics:
    """Metrics for a single API call"""
    """Aggregated metrics for reporting"""
        default_factory=lambda: defaultdict(lambda: {"input": 0, "output": 0})
    )
    cost_by_model: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    errors_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

class ClaudeMonitor:
    """
    """
        storage_backend: Optional[str] = "memory",  # memory, redis, mongodb
    ):
        self.log_responses = log_responses
        self.log_prompts = log_prompts
        self.alert_threshold_cost = alert_threshold_cost
        self.alert_threshold_errors = alert_threshold_errors
        self.storage_backend = storage_backend

        # In-memory storage for now
        self.metrics: List[APICallMetrics] = []
        self.consecutive_errors = 0
        self.session_costs: Dict[str, float] = defaultdict(float)

        # Initialize storage backend
        self._init_storage()

        logger.info(
            "Claude monitoring initialized",
            extra={
                "log_responses": log_responses,
                "log_prompts": log_prompts,
                "alert_threshold_cost": alert_threshold_cost,
                "storage_backend": storage_backend,
            },
        )

    def _init_storage(self):
        """Initialize the storage backend"""
        if self.storage_backend == "redis":
            # TODO: Initialize Redis connection
            pass
        elif self.storage_backend == "mongodb":
            # TODO: Initialize mongodb client
            pass
        # Default to in-memory storage

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost for a Claude API call"""
            logger.warning(f"Unknown model {model}, using default pricing")
            # Use Claude 3 Sonnet as default pricing
            pricing = CLAUDE_PRICING["claude-3-sonnet-20240229"]
        else:
            pricing = CLAUDE_PRICING[model]

        # Calculate cost (prices are per 1M tokens)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        return round(total_cost, 6)

    @asynccontextmanager
    async def monitor_call(
        self,
        model: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
            async with monitor.monitor_call(model="claude-3-opus") as ctx:
                response = await claude_api_call()
                ctx.set_tokens(response.usage)
        """
        request_id = f"claude_{int(time.time() * 1000000)}"
        start_time = time.time()

        class CallContext:
            def __init__(self, monitor, request_id):
                self.monitor = monitor
                self.request_id = request_id
                self.input_tokens = 0
                self.output_tokens = 0
                self.error = None

            def set_tokens(self, usage: Dict[str, int]):
                self.input_tokens = usage.get("prompt_tokens", 0)
                self.output_tokens = usage.get("completion_tokens", 0)

            def set_error(self, error: Exception):
                self.error = error

        ctx = CallContext(self, request_id)

        try:


            pass
            yield ctx

            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            total_tokens = ctx.input_tokens + ctx.output_tokens
            cost_usd = self.calculate_cost(model, ctx.input_tokens, ctx.output_tokens)

            # Create metrics record
            metrics = APICallMetrics(
                request_id=request_id,
                model=model,
                timestamp=datetime.now(timezone.utc),
                input_tokens=ctx.input_tokens,
                output_tokens=ctx.output_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                status="success",
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {},
            )

            # Store metrics
            await self._store_metrics(metrics)

            # Reset error counter on success
            self.consecutive_errors = 0

            # Check cost alerts
            if session_id:
                self.session_costs[session_id] += cost_usd
                if self.session_costs[session_id] > self.alert_threshold_cost:
                    await self._send_cost_alert(session_id, self.session_costs[session_id])

        except Exception:


            pass
            # Record error metrics
            latency_ms = (time.time() - start_time) * 1000

            metrics = APICallMetrics(
                request_id=request_id,
                model=model,
                timestamp=datetime.now(timezone.utc),
                input_tokens=ctx.input_tokens,
                output_tokens=ctx.output_tokens,
                total_tokens=ctx.input_tokens + ctx.output_tokens,
                latency_ms=latency_ms,
                cost_usd=0.0,
                status="error",
                error_message=str(e),
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {},
            )

            await self._store_metrics(metrics)

            # Track consecutive errors
            self.consecutive_errors += 1
            if self.consecutive_errors >= self.alert_threshold_errors:
                await self._send_error_alert(model, self.consecutive_errors)

            # Re-raise the exception
            raise

    async def _store_metrics(self, metrics: APICallMetrics):
        """Store metrics in the configured backend"""
            "Claude API call completed",
            extra={
                "request_id": metrics.request_id,
                "model": metrics.model,
                "status": metrics.status,
                "input_tokens": metrics.input_tokens,
                "output_tokens": metrics.output_tokens,
                "cost_usd": metrics.cost_usd,
                "latency_ms": metrics.latency_ms,
                "user_id": metrics.user_id,
                "session_id": metrics.session_id,
                "error": metrics.error_message,
            },
        )

        # Store in persistent backend
        if self.storage_backend == "redis":
            # TODO: Store in Redis
            pass
        elif self.storage_backend == "mongodb":
            # TODO: Store in mongodb
            pass

    async def _send_cost_alert(self, session_id: str, total_cost: float):
        """Send alert when cost threshold is exceeded"""
            f"Cost threshold exceeded for session {session_id}",
            extra={
                "session_id": session_id,
                "total_cost_usd": total_cost,
                "threshold_usd": self.alert_threshold_cost,
            },
        )
        # TODO: Send actual alert (email, Slack, etc.)

    async def _send_error_alert(self, model: str, error_count: int):
        """Send alert when error threshold is exceeded"""
            f"Error threshold exceeded for model {model}",
            extra={
                "model": model,
                "consecutive_errors": error_count,
                "threshold": self.alert_threshold_errors,
            },
        )
        # TODO: Send actual alert (email, Slack, etc.)

    def get_metrics_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AggregatedMetrics:
        """
        """
            if metric.status == "success":
                summary.successful_calls += 1
            else:
                summary.failed_calls += 1
                if metric.error_message:
                    error_type = metric.error_message.split(":")[0]
                    summary.errors_by_type[error_type] += 1

            summary.total_input_tokens += metric.input_tokens
            summary.total_output_tokens += metric.output_tokens
            summary.total_cost_usd += metric.cost_usd
            total_latency += metric.latency_ms

            # By model aggregations
            summary.calls_by_model[metric.model] += 1
            summary.tokens_by_model[metric.model]["input"] += metric.input_tokens
            summary.tokens_by_model[metric.model]["output"] += metric.output_tokens
            summary.cost_by_model[metric.model] += metric.cost_usd

        # Calculate averages
        if summary.total_calls > 0:
            summary.average_latency_ms = total_latency / summary.total_calls

        return summary

    def export_metrics(
        self,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Union[str, List[Dict[str, Any]]]:
        """
        """
        if format == "json":
            return json.dumps(
                [
                    {
                        "request_id": m.request_id,
                        "model": m.model,
                        "timestamp": m.timestamp.isoformat(),
                        "input_tokens": m.input_tokens,
                        "output_tokens": m.output_tokens,
                        "total_tokens": m.total_tokens,
                        "latency_ms": m.latency_ms,
                        "cost_usd": m.cost_usd,
                        "status": m.status,
                        "error_message": m.error_message,
                        "user_id": m.user_id,
                        "session_id": m.session_id,
                        "metadata": m.metadata,
                    }
                    # TODO: Consider using list comprehension for better performance

                    for m in filtered_metrics
                ],
                indent=2,
            )

        elif format == "csv":
            # Simple CSV export
            lines = [
                "request_id,model,timestamp,input_tokens,output_tokens,total_tokens,latency_ms,cost_usd,status,error_message,user_id,session_id"
            ]
            for m in filtered_metrics:
                lines.append(
                    f"{m.request_id},{m.model},{m.timestamp.isoformat()},{m.input_tokens},"
                    f"{m.output_tokens},{m.total_tokens},{m.latency_ms},{m.cost_usd},"
                    f"{m.status},{m.error_message or ''},{m.user_id or ''},{m.session_id or ''}"
                )
            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported format: {format}")
