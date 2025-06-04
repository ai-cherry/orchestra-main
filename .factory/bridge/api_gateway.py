import os
"""
"""
    """Available Factory AI Droid types."""
    ARCHITECT = "architect"
    CODE = "code"
    DEBUG = "debug"
    RELIABILITY = "reliability"
    KNOWLEDGE = "knowledge"

class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class CircuitBreakerState:
    """Circuit breaker state for fault tolerance."""
    """Request model for Factory AI operations."""
    """Response model for Factory AI operations."""
    """Main gateway for Factory AI Bridge operations."""
        factory_base_url: str = "https://api.factoryai.com/v1",
        mcp_servers: Optional[Dict[str, str]] = None,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
    ):
        """
        """
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
        }

        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
                "Authorization": f"Bearer {self.factory_api_key}",
                "Content-Type": "application/json",
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        """
        """
        """Record successful request for circuit breaker."""
        """Record failed request for circuit breaker."""
            logger.warning(f"Circuit breaker opened for {droid}")

    async def process_request(self, request: FactoryRequest) -> FactoryResponse:
        """
        """
                detail=f"Circuit breaker open for {request.droid}",
            )

        task_id = uuid4()
        self.active_requests[task_id] = request
        start_time = time.time()

        try:


            pass
            # Update metrics
            self.metrics["total_requests"] += 1

            # Prepare request payload
            payload = {
                "droid": request.droid.value,
                "task": request.task,
                "context": request.context,
                "options": request.options,
                "priority": request.priority,
            }

            # Make request to Factory AI
            async with self.session.post(
                f"{self.factory_base_url}/droids/{request.droid.value}/execute",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=request.timeout),
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    processing_time = time.time() - start_time

                    # Record success
                    self._record_success(request.droid)
                    self.metrics["successful_requests"] += 1
                    self._update_average_response_time(processing_time)

                    factory_response = FactoryResponse(
                        task_id=str(task_id),
                        status=TaskStatus.COMPLETED,
                        result=result,
                        processing_time=processing_time,
                        metadata={
                            "droid": request.droid.value,
                            "task": request.task,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )

                    # Store in history
                    self.request_history.append((task_id, factory_response))
                    if len(self.request_history) > 1000:
                        self.request_history.pop(0)

                    return factory_response

                else:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Factory AI error: {error_text}",
                    )

        except Exception:


            pass
            self._record_failure(request.droid)
            self.metrics["failed_requests"] += 1
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Request timeout after {request.timeout} seconds",
            )

        except Exception:


            pass
            self._record_failure(request.droid)
            self.metrics["failed_requests"] += 1
            logger.error(f"Request processing error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

        finally:
            # Clean up active request
            self.active_requests.pop(task_id, None)

    async def fallback_to_mcp(self, request: FactoryRequest) -> FactoryResponse:
        """
        """
                detail=f"No MCP fallback configured for {request.droid}",
            )

        # Transform request for MCP
        mcp_payload = self._transform_to_mcp_format(request)

        try:


            pass
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    mcp_endpoint,
                    json=mcp_payload,
                    timeout=aiohttp.ClientTimeout(total=request.timeout),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return FactoryResponse(
                            task_id=str(uuid4()),
                            status=TaskStatus.COMPLETED,
                            result=self._transform_from_mcp_format(result),
                            metadata={
                                "fallback": True,
                                "mcp_server": mcp_endpoint,
                            },
                        )
                    else:
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"MCP fallback error: {await response.text()}",
                        )

        except Exception:


            pass
            logger.error(f"MCP fallback error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MCP fallback failed: {str(e)}",
            )

    def _transform_to_mcp_format(self, request: FactoryRequest) -> Dict[str, Any]:
        """Transform Factory AI request to MCP format."""
            "method": f"{request.droid.value}.{request.task}",
            "params": {
                "context": request.context,
                "options": request.options,
            },
            "id": str(uuid4()),
        }

    def _transform_from_mcp_format(self, mcp_response: Dict[str, Any]) -> Dict[str, Any]:
        """Transform MCP response to Factory AI format."""
        return mcp_response.get("result", {})

    def _update_average_response_time(self, new_time: float):
        """Update average response time metric."""
        total = self.metrics["successful_requests"]
        if total == 1:
            self.metrics["average_response_time"] = new_time
        else:
            current_avg = self.metrics["average_response_time"]
            self.metrics["average_response_time"] = (current_avg * (total - 1) + new_time) / total

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
            "circuit_breakers": {
                droid.value: {
                    "is_open": breaker.is_open,
                    "failures": breaker.failures,
                }
                for droid, breaker in self.circuit_breakers.items()
            },
            "active_requests": len(self.active_requests),
        }

    def get_request_history(self, limit: int = 100) -> List[Tuple[str, FactoryResponse]]:
        """Get recent request history."""
    title="Factory AI Bridge Gateway",
    version="1.0.0",
    description="Bridge between Factory AI Droids and MCP infrastructure",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global gateway instance (initialized on startup)
gateway: Optional[FactoryBridgeGateway] = None

@app.on_event("startup")
async def startup_event():
    """Initialize gateway on startup."""
        factory_api_key= os.getenv('API_KEY'),
        mcp_servers={
            DroidType.ARCHITECT: "http://localhost:8001/mcp/conductor",
            DroidType.CODE: "http://localhost:8002/mcp/tools",
            DroidType.DEBUG: "http://localhost:8002/mcp/tools",
            DroidType.RELIABILITY: "http://localhost:8003/mcp/deployment",
            DroidType.KNOWLEDGE: "http://localhost:8004/mcp/memory",
        },
    )

@app.post("/api/v1/execute", response_model=FactoryResponse)
async def execute_task(request: FactoryRequest) -> FactoryResponse:
    """Execute a Factory AI task."""
            detail="Gateway not initialized",
        )

    try:


        pass
        async with gateway:
            return await gateway.process_request(request)
    except Exception:

        pass
        # Try fallback to MCP
        try:

            pass
            async with gateway:
                return await gateway.fallback_to_mcp(request)
        except Exception:

            pass
            raise

@app.get("/api/v1/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get gateway performance metrics."""
        return {"error": "Gateway not initialized"}
    return gateway.get_metrics()

@app.get("/api/v1/history")
async def get_history(limit: int = 100) -> List[Dict[str, Any]]:
    """Get request history."""
        {"task_id": task_id, "response": response.dict()} for task_id, response in gateway.get_request_history(limit)
    ]

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
