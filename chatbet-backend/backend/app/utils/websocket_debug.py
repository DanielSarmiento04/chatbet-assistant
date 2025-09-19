"""
WebSocket debugging utilities for development and testing.

This module provides debugging tools for WebSocket connections,
message inspection, performance monitoring, and troubleshooting.
"""

import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque

from ..core.logging import get_logger
from ..models.websocket_models import WSBaseMessage

logger = get_logger(__name__)


class WebSocketDebugger:
    """
    WebSocket debugging and monitoring utility.
    
    This class provides tools for monitoring WebSocket connections,
    analyzing message patterns, and debugging performance issues.
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        
        # Message history tracking
        self.message_history: deque = deque(maxlen=max_history)
        self.connection_events: deque = deque(maxlen=max_history)
        
        # Performance tracking
        self.performance_metrics = {
            "total_messages": 0,
            "total_connections": 0,
            "total_disconnections": 0,
            "message_types": defaultdict(int),
            "session_stats": defaultdict(dict),
            "error_count": 0,
            "start_time": datetime.utcnow()
        }
        
        # Connection tracking
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        
        # Message analysis
        self.message_patterns = defaultdict(int)
        self.response_times = deque(maxlen=100)
    
    def log_connection(self, session_id: str, connection_info: Dict[str, Any]):
        """Log a new WebSocket connection."""
        timestamp = datetime.utcnow()
        
        event = {
            "type": "connection",
            "session_id": session_id,
            "timestamp": timestamp,
            "info": connection_info
        }
        
        self.connection_events.append(event)
        self.active_connections[session_id] = {
            "connected_at": timestamp,
            "messages_sent": 0,
            "messages_received": 0,
            "last_activity": timestamp,
            "info": connection_info
        }
        
        self.performance_metrics["total_connections"] += 1
        
        logger.debug(
            f"WebSocket connection logged: {session_id}",
            extra={"session_id": session_id, "connection_info": connection_info}
        )
    
    def log_disconnection(self, session_id: str, reason: str = "unknown"):
        """Log a WebSocket disconnection."""
        timestamp = datetime.utcnow()
        
        event = {
            "type": "disconnection",
            "session_id": session_id,
            "timestamp": timestamp,
            "reason": reason
        }
        
        self.connection_events.append(event)
        
        # Update connection stats
        if session_id in self.active_connections:
            connection_info = self.active_connections[session_id]
            duration = timestamp - connection_info["connected_at"]
            
            self.performance_metrics["session_stats"][session_id] = {
                "duration_seconds": duration.total_seconds(),
                "messages_sent": connection_info["messages_sent"],
                "messages_received": connection_info["messages_received"],
                "disconnection_reason": reason
            }
            
            del self.active_connections[session_id]
        
        self.performance_metrics["total_disconnections"] += 1
        
        logger.debug(
            f"WebSocket disconnection logged: {session_id}",
            extra={"session_id": session_id, "reason": reason}
        )
    
    def log_message(
        self, 
        session_id: str, 
        message: Any, 
        direction: str = "inbound",
        processing_time: Optional[float] = None
    ):
        """
        Log a WebSocket message.
        
        Args:
            session_id: Session that sent/received the message
            message: The message content
            direction: 'inbound' or 'outbound'
            processing_time: Time taken to process the message (seconds)
        """
        timestamp = datetime.utcnow()
        
        # Parse message type
        message_type = "unknown"
        if isinstance(message, dict):
            message_type = message.get("type", "unknown")
        elif hasattr(message, "type"):
            message_type = message.type
        
        # Create message entry
        entry = {
            "timestamp": timestamp,
            "session_id": session_id,
            "direction": direction,
            "message_type": message_type,
            "message": message,
            "processing_time": processing_time,
            "size_bytes": len(str(message))
        }
        
        self.message_history.append(entry)
        
        # Update metrics
        self.performance_metrics["total_messages"] += 1
        self.performance_metrics["message_types"][message_type] += 1
        
        if processing_time:
            self.response_times.append(processing_time)
        
        # Update connection stats
        if session_id in self.active_connections:
            connection = self.active_connections[session_id]
            connection["last_activity"] = timestamp
            
            if direction == "inbound":
                connection["messages_received"] += 1
            else:
                connection["messages_sent"] += 1
        
        # Analyze message patterns
        pattern_key = f"{direction}:{message_type}"
        self.message_patterns[pattern_key] += 1
        
        logger.debug(
            f"WebSocket message logged: {direction} {message_type}",
            extra={
                "session_id": session_id,
                "message_type": message_type,
                "direction": direction,
                "processing_time": processing_time
            }
        )
    
    def log_error(self, session_id: str, error: Exception, context: str = ""):
        """Log a WebSocket error."""
        timestamp = datetime.utcnow()
        
        entry = {
            "timestamp": timestamp,
            "session_id": session_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        
        self.message_history.append(entry)
        self.performance_metrics["error_count"] += 1
        
        logger.error(
            f"WebSocket error logged: {error}",
            extra={
                "session_id": session_id,
                "error_type": type(error).__name__,
                "context": context
            },
            exc_info=error
        )
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics."""
        now = datetime.utcnow()
        uptime = now - self.performance_metrics["start_time"]
        
        avg_response_time = 0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "active_connections": len(self.active_connections),
            "total_connections": self.performance_metrics["total_connections"],
            "total_disconnections": self.performance_metrics["total_disconnections"],
            "total_messages": self.performance_metrics["total_messages"],
            "error_count": self.performance_metrics["error_count"],
            "average_response_time": avg_response_time,
            "message_types": dict(self.performance_metrics["message_types"]),
            "message_patterns": dict(self.message_patterns),
            "messages_per_second": self.performance_metrics["total_messages"] / max(uptime.total_seconds(), 1)
        }
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session."""
        if session_id not in self.active_connections:
            # Check if it's in completed sessions
            return self.performance_metrics["session_stats"].get(session_id)
        
        connection = self.active_connections[session_id]
        now = datetime.utcnow()
        duration = now - connection["connected_at"]
        
        return {
            "session_id": session_id,
            "connected_at": connection["connected_at"].isoformat(),
            "duration_seconds": duration.total_seconds(),
            "messages_sent": connection["messages_sent"],
            "messages_received": connection["messages_received"],
            "last_activity": connection["last_activity"].isoformat(),
            "connection_info": connection["info"]
        }
    
    def get_recent_messages(self, limit: int = 50, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent messages, optionally filtered by session."""
        messages = list(self.message_history)
        
        if session_id:
            messages = [msg for msg in messages if msg.get("session_id") == session_id]
        
        # Sort by timestamp (most recent first)
        messages.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        
        # Convert timestamps to ISO format for JSON serialization
        for msg in messages[:limit]:
            if "timestamp" in msg and isinstance(msg["timestamp"], datetime):
                msg["timestamp"] = msg["timestamp"].isoformat()
        
        return messages[:limit]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        error_messages = [
            msg for msg in self.message_history 
            if msg.get("error_type")
        ]
        
        error_types = defaultdict(int)
        for error in error_messages:
            error_types[error.get("error_type", "unknown")] += 1
        
        return {
            "total_errors": len(error_messages),
            "error_types": dict(error_types),
            "recent_errors": error_messages[-10:]  # Last 10 errors
        }
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze WebSocket performance metrics."""
        stats = self.get_connection_stats()
        
        # Calculate percentiles for response times
        response_times = sorted(self.response_times)
        percentiles = {}
        if response_times:
            for p in [50, 90, 95, 99]:
                idx = int(len(response_times) * p / 100)
                if idx < len(response_times):
                    percentiles[f"p{p}"] = response_times[idx]
        
        # Connection stability
        connection_stability = 0
        if stats["total_connections"] > 0:
            connection_stability = (stats["total_connections"] - stats["error_count"]) / stats["total_connections"]
        
        return {
            "response_time_percentiles": percentiles,
            "connection_stability": connection_stability,
            "error_rate": stats["error_count"] / max(stats["total_messages"], 1),
            "average_session_duration": self._calculate_average_session_duration(),
            "peak_concurrent_connections": self._get_peak_connections(),
            "recommendations": self._generate_recommendations(stats)
        }
    
    def _calculate_average_session_duration(self) -> float:
        """Calculate average session duration."""
        completed_sessions = self.performance_metrics["session_stats"]
        if not completed_sessions:
            return 0
        
        total_duration = sum(
            session["duration_seconds"] 
            for session in completed_sessions.values()
        )
        return total_duration / len(completed_sessions)
    
    def _get_peak_connections(self) -> int:
        """Get peak concurrent connections (simplified)."""
        # In a real implementation, you'd track this over time
        return max(len(self.active_connections), self.performance_metrics["total_connections"])
    
    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        if stats["error_count"] > stats["total_messages"] * 0.05:  # >5% error rate
            recommendations.append("High error rate detected. Check error logs and message validation.")
        
        if stats["average_response_time"] > 1.0:  # >1 second average
            recommendations.append("High response times. Consider optimizing message processing.")
        
        if len(self.active_connections) > 100:
            recommendations.append("High number of concurrent connections. Monitor resource usage.")
        
        if stats["messages_per_second"] > 100:
            recommendations.append("High message throughput. Consider implementing rate limiting.")
        
        return recommendations
    
    def export_debug_data(self) -> Dict[str, Any]:
        """Export all debug data for external analysis."""
        return {
            "stats": self.get_connection_stats(),
            "performance": self.analyze_performance(),
            "recent_messages": self.get_recent_messages(100),
            "error_summary": self.get_error_summary(),
            "active_sessions": {
                sid: self.get_session_info(sid) 
                for sid in self.active_connections.keys()
            }
        }
    
    def clear_history(self):
        """Clear message and connection history."""
        self.message_history.clear()
        self.connection_events.clear()
        self.response_times.clear()
        
        # Reset metrics but keep start time
        start_time = self.performance_metrics["start_time"]
        self.performance_metrics.clear()
        self.performance_metrics.update({
            "total_messages": 0,
            "total_connections": 0,
            "total_disconnections": 0,
            "message_types": defaultdict(int),
            "session_stats": defaultdict(dict),
            "error_count": 0,
            "start_time": start_time
        })
        
        self.message_patterns.clear()
        
        logger.info("WebSocket debug history cleared")


# Global debugger instance
_websocket_debugger: Optional[WebSocketDebugger] = None


def get_websocket_debugger() -> WebSocketDebugger:
    """Get global WebSocket debugger instance."""
    global _websocket_debugger
    if _websocket_debugger is None:
        _websocket_debugger = WebSocketDebugger()
    return _websocket_debugger


def debug_message(session_id: str, message: Any, direction: str = "inbound", processing_time: Optional[float] = None):
    """Convenience function to log a message."""
    debugger = get_websocket_debugger()
    debugger.log_message(session_id, message, direction, processing_time)


def debug_connection(session_id: str, connection_info: Dict[str, Any]):
    """Convenience function to log a connection."""
    debugger = get_websocket_debugger()
    debugger.log_connection(session_id, connection_info)


def debug_disconnection(session_id: str, reason: str = "unknown"):
    """Convenience function to log a disconnection."""
    debugger = get_websocket_debugger()
    debugger.log_disconnection(session_id, reason)


def debug_error(session_id: str, error: Exception, context: str = ""):
    """Convenience function to log an error."""
    debugger = get_websocket_debugger()
    debugger.log_error(session_id, error, context)