"""
WebSocket streaming callback for LangChain integration.

This module provides a custom LangChain callback handler that streams
LLM responses in real-time over WebSocket connections, enabling
word-by-word response generation for the ChatBet assistant.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Sequence, Union
from uuid import uuid4, UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

from ..core.logging import get_logger
from ..models.websocket_models import (
    WSStreamingResponse, WSStreamingStart, WSStreamingEnd, WSBotResponse,
    WebSocketMessageType
)
from ..services.websocket_manager import WebSocketConnectionManager

logger = get_logger(__name__)


class WebSocketStreamingCallback(AsyncCallbackHandler):
    """
    Custom LangChain callback for streaming LLM responses to WebSocket.
    
    This callback handler intercepts token generation from LangChain LLMs
    and streams them in real-time to connected WebSocket clients, providing
    a smooth typing experience for users.
    """
    
    def __init__(
        self,
        websocket_manager: WebSocketConnectionManager,
        session_id: str,
        message_id: Optional[str] = None,
        chunk_size: int = 1,
        delay_between_chunks: float = 0.05
    ):
        """
        Initialize the streaming callback.
        
        Args:
            websocket_manager: WebSocket connection manager instance
            session_id: Session ID to stream to
            message_id: Optional message ID (generates new if None)
            chunk_size: Number of tokens per chunk (default: 1 for word-by-word)
            delay_between_chunks: Delay between chunks in seconds
        """
        super().__init__()
        
        self.websocket_manager = websocket_manager
        self.session_id = session_id
        self.message_id = message_id or str(uuid4())
        self.chunk_size = chunk_size
        self.delay_between_chunks = delay_between_chunks
        
        # Streaming state
        self.content_buffer = ""
        self.token_buffer = []
        self.chunk_index = 0
        self.start_time: Optional[float] = None
        self.total_tokens = 0
        self.is_streaming = False
        
        # Performance tracking
        self.first_token_time: Optional[float] = None
        self.last_token_time: Optional[float] = None
    
    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts generating."""
        self.start_time = time.time()
        self.is_streaming = True
        
        logger.debug(
            f"Starting LLM streaming for session {self.session_id}",
            extra={
                "message_id": self.message_id,
                "prompts_count": len(prompts)
            }
        )
        
        # Send streaming start notification
        await self.websocket_manager.start_streaming_response(
            session_id=self.session_id,
            estimated_tokens=None  # Could estimate based on prompt length
        )
    
    async def on_llm_new_token(
        self, 
        token: str, 
        *, 
        chunk: Optional[Any] = None,
        run_id: Optional[UUID] = None,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any
    ) -> None:
        """
        Called when LLM generates a new token.
        
        This is the core streaming functionality - each token is buffered
        and sent in chunks to provide smooth real-time response delivery.
        """
        if not self.is_streaming:
            return
        
        # Track timing for first token
        if self.first_token_time is None:
            self.first_token_time = time.time()
        
        self.last_token_time = time.time()
        self.total_tokens += 1
        
        # Add token to buffer
        self.token_buffer.append(token)
        self.content_buffer += token
        
        # Send chunk when buffer reaches chunk_size or if it's a natural break
        if (len(self.token_buffer) >= self.chunk_size or 
            self._is_natural_break(token)):
            
            chunk_content = "".join(self.token_buffer)
            
            # Send streaming chunk
            await self.websocket_manager.send_streaming_chunk(
                session_id=self.session_id,
                content=chunk_content,
                full_content=self.content_buffer,
                chunk_index=self.chunk_index,
                is_final=False
            )
            
            # Clear token buffer and increment chunk index
            self.token_buffer.clear()
            self.chunk_index += 1
            
            # Optional delay for better UX (makes streaming feel more natural)
            if self.delay_between_chunks > 0:
                await asyncio.sleep(self.delay_between_chunks)
        
        logger.debug(
            f"Token streamed",
            extra={
                "session_id": self.session_id,
                "token_count": self.total_tokens,
                "chunk_index": self.chunk_index,
                "token": token[:20] + "..." if len(token) > 20 else token
            }
        )
    
    async def on_llm_end(
        self, 
        response: LLMResult, 
        *, 
        run_id: Optional[UUID] = None,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any
    ) -> None:
        """Called when LLM finishes generating."""
        if not self.is_streaming:
            return
        
        end_time = time.time()
        if self.start_time is None:
            return
            
        total_time_ms = int((end_time - self.start_time) * 1000)
        
        # Send any remaining tokens in buffer
        if self.token_buffer:
            final_chunk = "".join(self.token_buffer)
            self.content_buffer += final_chunk
            
            await self.websocket_manager.send_streaming_chunk(
                session_id=self.session_id,
                content=final_chunk,
                full_content=self.content_buffer,
                chunk_index=self.chunk_index,
                is_final=True
            )
        
        # Send streaming end notification
        await self.websocket_manager.end_streaming_response(
            session_id=self.session_id,
            final_content=self.content_buffer,
            total_chunks=self.chunk_index + 1,
            response_time_ms=total_time_ms
        )
        
        # Send final bot response message for consistency with HTTP API
        bot_response = WSBotResponse(
            session_id=self.session_id,
            message_id=self.message_id,
            content=self.content_buffer,
            response_time_ms=total_time_ms,
            token_count=self.total_tokens,
            intent_confidence=None,
            is_final=True
        )
        
        await self.websocket_manager.send_message(self.session_id, bot_response)
        
        self.is_streaming = False
        
        # Log performance metrics
        first_token_latency = None
        if self.first_token_time and self.start_time:
            first_token_latency = int((self.first_token_time - self.start_time) * 1000)
        
        logger.info(
            f"Streaming completed for session {self.session_id}",
            extra={
                "message_id": self.message_id,
                "total_tokens": self.total_tokens,
                "total_chunks": self.chunk_index + 1,
                "response_time_ms": total_time_ms,
                "first_token_latency_ms": first_token_latency,
                "tokens_per_second": (
                    self.total_tokens / (total_time_ms / 1000) 
                    if total_time_ms > 0 else 0
                )
            }
        )
    
    async def on_llm_error(
        self, 
        error: BaseException, 
        *, 
        run_id: Optional[UUID] = None,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any
    ) -> None:
        """Called when LLM encounters an error."""
        if not self.is_streaming:
            return
        
        logger.error(
            f"LLM error during streaming for session {self.session_id}: {error}",
            extra={
                "message_id": self.message_id,
                "error_type": type(error).__name__
            }
        )
        
        # Send error message to client
        await self.websocket_manager.send_error(
            session_id=self.session_id,
            error_code="LLM_STREAMING_ERROR",
            error_message="An error occurred while generating the response",
            details={"error_type": type(error).__name__}
        )
        
        self.is_streaming = False
    
    def _is_natural_break(self, token: str) -> bool:
        """
        Determine if a token represents a natural break point for streaming.
        
        Natural breaks include punctuation marks that provide good stopping
        points for streaming chunks, improving readability.
        
        Args:
            token: Token to check
            
        Returns:
            True if token is a natural break point
        """
        # Common punctuation marks that are good break points
        break_points = {'.', '!', '?', ',', ';', ':', '\n', '(', ')', '[', ']'}
        
        # Check if token ends with or contains break points
        return any(bp in token for bp in break_points)
    
    @property
    def streaming_stats(self) -> Dict[str, Any]:
        """
        Get streaming performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.start_time:
            return {}
        
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        return {
            "total_tokens": self.total_tokens,
            "total_chunks": self.chunk_index,
            "elapsed_time_ms": int(elapsed_time * 1000),
            "tokens_per_second": self.total_tokens / elapsed_time if elapsed_time > 0 else 0,
            "first_token_latency_ms": (
                int((self.first_token_time - self.start_time) * 1000)
                if self.first_token_time else None
            ),
            "is_streaming": self.is_streaming,
            "content_length": len(self.content_buffer)
        }


class BatchStreamingCallback(AsyncCallbackHandler):
    """
    Streaming callback that batches multiple tokens before sending.
    
    This variant collects multiple tokens before sending chunks, which can
    be more efficient for fast LLMs but provides less smooth streaming.
    """
    
    def __init__(
        self,
        websocket_manager: WebSocketConnectionManager,
        session_id: str,
        message_id: Optional[str] = None,
        batch_size: int = 5,
        max_delay_ms: int = 100
    ):
        """
        Initialize the batch streaming callback.
        
        Args:
            websocket_manager: WebSocket connection manager
            session_id: Session ID to stream to
            message_id: Optional message ID
            batch_size: Number of tokens to batch before sending
            max_delay_ms: Maximum delay before sending partial batch
        """
        super().__init__()
        
        self.websocket_manager = websocket_manager
        self.session_id = session_id
        self.message_id = message_id or str(uuid4())
        self.batch_size = batch_size
        self.max_delay_ms = max_delay_ms
        
        self.content_buffer = ""
        self.token_batch = []
        self.chunk_index = 0
        self.start_time: Optional[float] = None
        self.last_batch_time: Optional[float] = None
        self.total_tokens = 0
        self.is_streaming = False
        
        # Background task for flushing batches
        self._flush_task = None
    
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """Called when LLM starts generating."""
        self.start_time = time.time()
        self.last_batch_time = self.start_time
        self.is_streaming = True
        
        # Start background flush task
        self._flush_task = asyncio.create_task(self._periodic_flush())
        
        await self.websocket_manager.start_streaming_response(
            session_id=self.session_id
        )
    
    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Called when LLM generates a new token."""
        if not self.is_streaming:
            return
        
        self.total_tokens += 1
        self.token_batch.append(token)
        self.content_buffer += token
        
        # Send batch if it reaches batch_size
        if len(self.token_batch) >= self.batch_size:
            await self._flush_batch()
    
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM finishes generating."""
        if not self.is_streaming:
            return
        
        # Flush any remaining tokens
        if self.token_batch:
            await self._flush_batch()
        
        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()
        
        end_time = time.time()
        if self.start_time is None:
            return
            
        total_time_ms = int((end_time - self.start_time) * 1000)
        
        await self.websocket_manager.end_streaming_response(
            session_id=self.session_id,
            final_content=self.content_buffer,
            total_chunks=self.chunk_index,
            response_time_ms=total_time_ms
        )
        
        self.is_streaming = False
    
    async def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        """Called when LLM encounters an error."""
        if self._flush_task:
            self._flush_task.cancel()
        
        await self.websocket_manager.send_error(
            session_id=self.session_id,
            error_code="LLM_BATCH_STREAMING_ERROR",
            error_message="Error during batch streaming"
        )
        
        self.is_streaming = False
    
    async def _flush_batch(self):
        """Flush current token batch."""
        if not self.token_batch or not self.is_streaming:
            return
        
        chunk_content = "".join(self.token_batch)
        
        await self.websocket_manager.send_streaming_chunk(
            session_id=self.session_id,
            content=chunk_content,
            full_content=self.content_buffer,
            chunk_index=self.chunk_index,
            is_final=False
        )
        
        self.token_batch.clear()
        self.chunk_index += 1
        self.last_batch_time = time.time()
    
    async def _periodic_flush(self):
        """Periodically flush batches based on time delay."""
        try:
            while self.is_streaming:
                await asyncio.sleep(self.max_delay_ms / 1000)
                
                current_time = time.time()
                if self.last_batch_time is None:
                    continue
                    
                time_since_last_batch = (current_time - self.last_batch_time) * 1000
                
                # Flush if we have tokens and enough time has passed
                if self.token_batch and time_since_last_batch >= self.max_delay_ms:
                    await self._flush_batch()
                    
        except asyncio.CancelledError:
            pass