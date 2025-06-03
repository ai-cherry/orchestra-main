"""
"""
    """
    """
        """
        """
    """
    """
    """
    """
    """
    """
    """
    """
    """
    """
    """Base API processor with common HTTP functionality."""
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.auth = auth
        self.timeout = ClientTimeout(total=timeout)
        self.rate_limit = rate_limit  # requests per second
        self._last_request_time: Optional[float] = None
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        """Apply rate limiting if configured."""
        """Make HTTP request with error handling."""
                kwargs["auth"] = aiohttp.BasicAuth(self.auth[0], self.auth[1])
            elif isinstance(self.auth, dict):
                if "bearer" in self.auth:
                    self.headers["Authorization"] = f"Bearer {self.auth['bearer']}"
                elif "api_key" in self.auth:
                    if "api_key_header" in self.auth:
                        self.headers[self.auth["api_key_header"]] = self.auth["api_key"]
                    else:
                        kwargs.setdefault("params", {})["api_key"] = self.auth["api_key"]

        # Apply rate limiting
        await self._apply_rate_limit()

        async with session.request(method, url, **kwargs) as response:
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return await response.json()
            else:
                text = await response.text()
                return {"raw_response": text}

    async def close(self) -> None:
        """Close the session."""
        return ["api", "rest", "http"]

class RESTAPIProcessor(APIProcessor):
    """Process data from REST APIs with pagination support."""
        method: str = "GET",
        endpoint: str = "",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        pagination_type: str = "none",  # 'none', 'offset', 'cursor', 'page'
        pagination_config: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[ProcessedData]:
        """Process data from REST API endpoint."""
        if isinstance(source, str) and source.startswith("http"):
            url = source
        else:
            url = urljoin(self.base_url, endpoint)

        # Pagination configuration
        page_config = pagination_config or {}
        page_param = page_config.get("page_param", "page")
        offset_param = page_config.get("offset_param", "offset")
        limit_param = page_config.get("limit_param", "limit")
        cursor_param = page_config.get("cursor_param", "cursor")
        results_path = page_config.get("results_path", None)
        next_cursor_path = page_config.get("next_cursor_path", "next_cursor")

        # Initialize pagination
        current_page = 1
        current_offset = 0
        current_cursor = None
        pages_processed = 0

        params = params or {}

        try:


            pass
            while True:
                # Apply pagination parameters
                request_params = params.copy()

                if pagination_type == "page":
                    request_params[page_param] = current_page
                elif pagination_type == "offset":
                    request_params[offset_param] = current_offset
                    if limit_param:
                        request_params[limit_param] = page_config.get("page_size", 100)
                elif pagination_type == "cursor" and current_cursor:
                    request_params[cursor_param] = current_cursor

                # Make request
                response_data = await self._make_request(
                    method,
                    url,
                    params=request_params,
                    json=data if method in ["POST", "PUT", "PATCH"] else None,
                )

                # Extract results
                if results_path:
                    # Navigate to results in nested structure
                    results = response_data
                    for key in results_path.split("."):
                        results = results.get(key, [])
                else:
                    results = response_data if isinstance(response_data, list) else [response_data]

                # Process results
                for idx, item in enumerate(results):
                    content = json.dumps(item, indent=2)
                    checksum = self.calculate_checksum(content)

                    yield ProcessedData(
                        raw_content=content,
                        processed_content=content,
                        source_type="rest_api",
                        source_url=url,
                        metadata={
                            "method": method,
                            "endpoint": endpoint,
                            "page": current_page if pagination_type == "page" else None,
                            "offset": (current_offset if pagination_type == "offset" else None),
                            "cursor": (current_cursor if pagination_type == "cursor" else None),
                            "item_index": idx,
                            "response_keys": (list(item.keys()) if isinstance(item, dict) else []),
                        },
                        checksum=checksum,
                        processing_stats={
                            "pages_processed": pages_processed + 1,
                            "items_in_page": len(results),
                        },
                    )

                pages_processed += 1

                # Check if we've reached max pages
                if max_pages and pages_processed >= max_pages:
                    break

                # Check for more pages
                if pagination_type == "none":
                    break
                elif pagination_type == "page":
                    # Check if there are more results
                    if not results or len(results) < page_config.get("page_size", 100):
                        break
                    current_page += 1
                elif pagination_type == "offset":
                    if not results:
                        break
                    current_offset += len(results)
                elif pagination_type == "cursor":
                    # Extract next cursor
                    next_cursor = response_data
                    for key in next_cursor_path.split("."):
                        next_cursor = next_cursor.get(key) if isinstance(next_cursor, dict) else None

                    if not next_cursor:
                        break
                    current_cursor = next_cursor

        finally:
            await self.close()

class GraphQLProcessor(APIProcessor):
    """Process data from GraphQL APIs."""
        """Process data from GraphQL API."""
        if isinstance(source, str) and source.startswith("http"):
            url = source
        else:
            url = urljoin(self.base_url, source if isinstance(source, str) else "/graphql")

        # Prepare GraphQL request
        payload = {
            "query": query,
            "variables": variables or {},
        }
        if operation_name:
            payload["operationName"] = operation_name

        try:


            pass
            # Make request
            response_data = await self._make_request("POST", url, json=payload)

            # Check for errors
            if "errors" in response_data:
                errors_str = json.dumps(response_data["errors"], indent=2)
                yield ProcessedData(
                    raw_content=errors_str,
                    processed_content=f"GraphQL Errors: {errors_str}",
                    source_type="graphql_api",
                    source_url=url,
                    metadata={
                        "error_type": "graphql_errors",
                        "errors": response_data["errors"],
                        "query": query,
                        "variables": variables,
                    },
                    checksum=self.calculate_checksum(errors_str),
                )

            # Process data
            if "data" in response_data:
                data = response_data["data"]

                # Flatten nested structure for processing
                items = self._extract_items(data)

                for idx, item in enumerate(items):
                    content = json.dumps(item, indent=2)
                    checksum = self.calculate_checksum(content)

                    yield ProcessedData(
                        raw_content=content,
                        processed_content=content,
                        source_type="graphql_api",
                        source_url=url,
                        metadata={
                            "operation_name": operation_name,
                            "item_index": idx,
                            "query_hash": self.calculate_checksum(query)[:8],
                            "response_keys": (list(item.keys()) if isinstance(item, dict) else []),
                        },
                        checksum=checksum,
                        processing_stats={
                            "total_items": len(items),
                        },
                    )

        finally:
            await self.close()

    def _extract_items(self, data: Any, items: Optional[List[Any]] = None) -> List[Any]:
        """Extract individual items from nested GraphQL response."""
    """Process streaming data from WebSocket connections."""
        return ["websocket", "ws", "wss"]

    async def process(
        self,
        source: Union[str, Path, bytes],
        message_handler: Optional[callable] = None,
        max_messages: Optional[int] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> AsyncIterator[ProcessedData]:
        """Process streaming data from WebSocket."""
                                    parsed_data = {"raw_message": data}
                                    content = data

                                # Apply custom message handler if provided
                                if message_handler:
                                    parsed_data = message_handler(parsed_data)

                                checksum = self.calculate_checksum(content)
                                messages_processed += 1

                                yield ProcessedData(
                                    raw_content=data,
                                    processed_content=content,
                                    source_type="websocket",
                                    source_url=ws_url,
                                    metadata={
                                        "message_type": "text",
                                        "message_number": messages_processed,
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "data_keys": (
                                            list(parsed_data.keys()) if isinstance(parsed_data, dict) else []
                                        ),
                                    },
                                    checksum=checksum,
                                    processing_stats={
                                        "total_messages": messages_processed,
                                        "connection_duration": asyncio.get_event_loop().time() - start_time,
                                    },
                                )

                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                yield ProcessedData(
                                    raw_content=str(ws.exception()),
                                    processed_content=f"WebSocket Error: {ws.exception()}",
                                    source_type="websocket",
                                    source_url=ws_url,
                                    metadata={
                                        "error_type": "websocket_error",
                                        "error": str(ws.exception()),
                                    },
                                    checksum="",
                                )
                                break

                # Exit loop if we completed successfully
                break

            except Exception:


                pass
                reconnect_attempts += 1

                yield ProcessedData(
                    raw_content="",
                    processed_content=f"Connection Error: {str(e)}",
                    source_type="websocket",
                    source_url=ws_url,
                    metadata={
                        "error_type": "connection_error",
                        "error": str(e),
                        "reconnect_attempt": reconnect_attempts,
                    },
                    checksum="",
                )

                if self.reconnect_on_error and reconnect_attempts < self.max_reconnect_attempts:
                    # Wait before reconnecting
                    await asyncio.sleep(min(reconnect_attempts * 2, 30))
                else:
                    break
