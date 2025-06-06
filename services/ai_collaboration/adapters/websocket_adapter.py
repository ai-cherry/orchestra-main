#!/usr/bin/env python3
"""
WebSocket Adapter for AI Collaboration Bridge
Implements circuit breaker pattern and automatic reconnection
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from enum import Enum

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    from websockets.exceptions import WebSocketException
except ImportError:
    # Mock websockets for when the library is not installed
    class WebSocketClientProtocol:
        pass
    
    class WebSocketException(Exception):
        pass
    
    class websockets:
        @staticmethod
        async def connect(*args, **kwargs):
            raise NotImplementedError("websockets library not installed. Install with: pip install websockets")
        
        class exceptions:
            ConnectionClosed = Exception

from ..interfaces import IWebSocketAdapter, ICircuitBreaker
from ..exceptions import (
    WebSocketConnectionError,
    CircuitBreakerOpenError,
    TemporaryError,
    SerializationError
)
from ..models.dto import WebSocketMessageDTO


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        logger: Optional[logging.Logger] = None
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.logger = logger or logging.getLogger(__name__)
        
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = CircuitBreakerState.CLOSED
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        if self._state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(
                    service="WebSocket",
                    failure_count=self._failure_count
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        return (
            self._last_failure_time is not None
            and datetime.utcnow() - self._last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
    
    def _on_success(self) -> None:
        """Handle successful call"""
        self._failure_count = 0
        self._state = CircuitBreakerState.CLOSED
        self._last_failure_time = None
    
    def _on_failure(self) -> None:
        """Handle failed call"""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()
        
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitBreakerState.OPEN
            self.logger.warning(
                f"Circuit breaker opened after {self._failure_count} failures"
            )
    
    def is_open(self) -> bool:
        """Check if circuit is open"""
        return self._state == CircuitBreakerState.OPEN
    
    def is_closed(self) -> bool:
        """Check if circuit is closed"""
        return self._state == CircuitBreakerState.CLOSED
    
    def get_state(self) -> str:
        """Get current state"""
        return self._state.value
    
    def get_failure_count(self) -> int:
        """Get current failure count"""
        return self._failure_count
    
    def reset(self) -> None:
        """Reset circuit breaker state"""
        self._failure_count = 0
        self._state = CircuitBreakerState.CLOSED
        self._last_failure_time = None


class CollaborationBridgeAdapter(IWebSocketAdapter):
    """
    WebSocket adapter for collaboration bridge with resilience patterns
    """
    
    def __init__(
        self,
        url: str = "ws://150.136.94.139:8765",
        logger: Optional[logging.Logger] = None
    ):
        self.url = url
        self.logger = logger or logging.getLogger(__name__)
        
        # Circuit breaker for connection resilience
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=WebSocketException,
            logger=self.logger
        )
        
        # Connection state
        self._websocket: Optional[WebSocketClientProtocol] = None
        self._connected = False
        self._reconnect_delay = 1
        self._max_reconnect_delay = 60
        self._reconnect_task: Optional[asyncio.Task] = None
        
        # Message handling
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self._message_handler: Optional[Callable] = None
        self._message_processor_task: Optional[asyncio.Task] = None
        
        # Metrics
        self._messages_sent = 0
        self._messages_received = 0
        self._connection_attempts = 0
        self._last_ping_time: Optional[datetime] = None
        self._last_pong_time: Optional[datetime] = None
    
    async def connect(self) -> None:
        """Connect to WebSocket endpoint with automatic reconnection"""
        if self._connected:
            self.logger.warning("Already connected to WebSocket")
            return
        
        # Start reconnection loop
        self._reconnect_task = asyncio.create_task(self._reconnection_loop())
        
        # Start message processor
        self._message_processor_task = asyncio.create_task(self._process_message_queue())
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket"""
        self._connected = False
        
        # Cancel tasks
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
        
        if self._message_processor_task:
            self._message_processor_task.cancel()
            try:
                await self._message_processor_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
        
        self.logger.info("Disconnected from WebSocket")
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send message through WebSocket"""
        if not self._connected:
            # Queue message for later delivery
            await self._message_queue.put(message)
            return
        
        try:
            # Create WebSocket message DTO
            ws_message = WebSocketMessageDTO(
                message_type=message.get("type", "unknown"),
                payload=message,
                correlation_id=message.get("correlation_id")
            )
            
            # Send message
            await self._websocket.send(ws_message.to_json())
            self._messages_sent += 1
            
            self.logger.debug(f"Sent message: {ws_message.message_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            # Re-queue message
            await self._message_queue.put(message)
            raise TemporaryError(f"Failed to send message: {e}")
    
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive message from WebSocket"""
        if not self._connected or not self._websocket:
            return None
        
        try:
            message_data = await self._websocket.recv()
            self._messages_received += 1
            
            # Parse message
            message = json.loads(message_data)
            
            # Handle through message handler if set
            if self._message_handler:
                await self._message_handler(message)
            
            return message
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse message: {e}")
            raise SerializationError("WebSocket message", str(e))
        except Exception as e:
            self.logger.error(f"Failed to receive message: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self._connected and self._websocket is not None
    
    async def ping(self) -> bool:
        """Send ping and wait for pong"""
        if not self._connected or not self._websocket:
            return False
        
        try:
            self._last_ping_time = datetime.utcnow()
            pong_waiter = await self._websocket.ping()
            await asyncio.wait_for(pong_waiter, timeout=10)
            self._last_pong_time = datetime.utcnow()
            return True
        except Exception as e:
            self.logger.warning(f"Ping failed: {e}")
            return False
    
    def set_message_handler(self, handler: Callable) -> None:
        """Set handler for incoming messages"""
        self._message_handler = handler
    
    # Private methods
    
    async def _reconnection_loop(self) -> None:
        """Continuous reconnection loop"""
        while True:
            try:
                await self._connect_with_retry()
                
                # Listen for messages
                await self._listen_for_messages()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Connection error: {e}")
                self._connected = False
                
                # Exponential backoff
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self._max_reconnect_delay
                )
    
    async def _connect_with_retry(self) -> None:
        """Connect with circuit breaker"""
        self._connection_attempts += 1
        
        try:
            await self.circuit_breaker.call(self._establish_connection)
            self._reconnect_delay = 1  # Reset on success
        except CircuitBreakerOpenError:
            self.logger.error("Circuit breaker is open, skipping connection attempt")
            raise
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            raise
    
    async def _establish_connection(self) -> None:
        """Establish WebSocket connection"""
        self.logger.info(f"Connecting to WebSocket at {self.url}")
        
        try:
            self._websocket = await websockets.connect(
                self.url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            self._connected = True
            self.logger.info("Connected to collaboration bridge")
            
            # Send any queued messages
            asyncio.create_task(self._flush_message_queue())
            
        except Exception as e:
            raise WebSocketConnectionError(self.url, str(e))
    
    async def _listen_for_messages(self) -> None:
        """Listen for incoming messages"""
        if not self._websocket:
            return
        
        try:
            async for message in self._websocket:
                await self.receive_message()
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
            self._connected = False
        except Exception as e:
            self.logger.error(f"Error listening for messages: {e}")
            self._connected = False
    
    async def _process_message_queue(self) -> None:
        """Process queued messages"""
        while True:
            try:
                # Wait for connection
                while not self._connected:
                    await asyncio.sleep(1)
                
                # Process queue
                message = await self._message_queue.get()
                await self.send_message(message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing message queue: {e}")
                await asyncio.sleep(1)
    
    async def _flush_message_queue(self) -> None:
        """Flush all queued messages"""
        flushed = 0
        while not self._message_queue.empty() and self._connected:
            try:
                message = self._message_queue.get_nowait()
                await self.send_message(message)
                flushed += 1
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                self.logger.error(f"Error flushing message: {e}")
        
        if flushed > 0:
            self.logger.info(f"Flushed {flushed} queued messages")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get adapter metrics"""
        return {
            "connected": self._connected,
            "messages_sent": self._messages_sent,
            "messages_received": self._messages_received,
            "connection_attempts": self._connection_attempts,
            "queue_size": self._message_queue.qsize(),
            "circuit_breaker_state": self.circuit_breaker.get_state(),
            "circuit_breaker_failures": self.circuit_breaker.get_failure_count(),
            "last_ping": self._last_ping_time.isoformat() if self._last_ping_time else None,
            "last_pong": self._last_pong_time.isoformat() if self._last_pong_time else None,
        }