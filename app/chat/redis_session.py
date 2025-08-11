from __future__ import annotations

import json
import time
from typing import Optional, Dict, Any
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

class RedisSessionManager:
    """Manages session persistence in Redis with TTL support."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", message_redis_url: Optional[str] = None, default_ttl: int = 3600):
        """
        Initialize Redis session manager.
        
        Args:
            redis_url: Redis connection URL for session data
            message_redis_url: Redis connection URL for message persistence (optional, uses redis_url if not provided)
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.redis_url = redis_url
        self.message_redis_url = message_redis_url or redis_url
        self.default_ttl = default_ttl
        self._redis_client: Optional[redis.Redis] = None
        self._message_redis_client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client for session data."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(self.redis_url)
        return self._redis_client
    
    async def _get_message_client(self) -> redis.Redis:
        """Get or create Redis client for message persistence."""
        if self._message_redis_client is None:
            self._message_redis_client = redis.from_url(self.message_redis_url)
        return self._message_redis_client
    
    async def store_session(self, session_id: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store session data in Redis with TTL.
        
        Args:
            session_id: Unique session identifier
            data: Session data to store
            ttl: TTL in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            key = f"session:{session_id}"
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            
            # Store session data as JSON
            session_data = {
                "data": data,
                "created_at": time.time(),
                "ttl": ttl_seconds
            }
            
            await client.setex(
                key,
                ttl_seconds,
                json.dumps(session_data)
            )
            
            logger.info(f"Session stored in Redis: {session_id}, TTL: {ttl_seconds}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store session {session_id} in Redis: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data from Redis.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session data if found and not expired, None otherwise
        """
        try:
            client = await self._get_client()
            key = f"session:{session_id}"
            
            data = await client.get(key)
            if data is None:
                return None
            
            session_data = json.loads(data)
            return session_data.get("data")
            
        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id} from Redis: {e}")
            return None
    
    async def update_session(self, session_id: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Update existing session data in Redis.
        
        Args:
            session_id: Unique session identifier
            data: Updated session data
            ttl: New TTL in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            key = f"session:{session_id}"
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            
            # Get existing session to preserve creation time
            existing_data = await client.get(key)
            created_at = time.time()
            
            if existing_data:
                try:
                    existing_session = json.loads(existing_data)
                    created_at = existing_session.get("created_at", created_at)
                except:
                    pass
            
            session_data = {
                "data": data,
                "created_at": created_at,
                "ttl": ttl_seconds
            }
            
            await client.setex(
                key,
                ttl_seconds,
                json.dumps(session_data)
            )
            
            logger.info(f"Session updated in Redis: {session_id}, TTL: {ttl_seconds}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id} in Redis: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session from Redis.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            key = f"session:{session_id}"
            
            result = await client.delete(key)
            if result:
                logger.info(f"Session deleted from Redis: {session_id}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id} from Redis: {e}")
            return False
    
    async def extend_session(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """
        Extend session TTL in Redis.
        
        Args:
            session_id: Unique session identifier
            ttl: New TTL in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            key = f"session:{session_id}"
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            
            # Get existing session data
            existing_data = await client.get(key)
            if existing_data is None:
                return False
            
            # Parse existing data
            session_data = json.loads(existing_data)
            
            # Update TTL
            session_data["ttl"] = ttl_seconds
            
            # Set with new TTL
            await client.setex(
                key,
                ttl_seconds,
                json.dumps(session_data)
            )
            
            logger.info(f"Session TTL extended in Redis: {session_id}, new TTL: {ttl_seconds}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extend session {session_id} TTL in Redis: {e}")
            return False
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information including TTL and creation time.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session info if found, None otherwise
        """
        try:
            client = await self._get_client()
            key = f"session:{session_id}"
            
            data = await client.get(key)
            if data is None:
                return None
            
            session_data = json.loads(data)
            ttl = await client.ttl(key)
            
            return {
                "data": session_data.get("data"),
                "created_at": session_data.get("created_at"),
                "ttl": session_data.get("ttl"),
                "remaining_ttl": ttl if ttl > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get session info {session_id} from Redis: {e}")
            return None
    
    async def close(self):
        """Close Redis connections."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
        if self._message_redis_client:
            await self._message_redis_client.close()
            self._message_redis_client = None

    # Message persistence methods using shared Redis
    async def store_message(self, session_id: str, message_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store a message in the shared message Redis instance.
        
        Args:
            session_id: Session identifier
            message_data: Message data to store
            ttl: TTL in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_message_client()
            messages_key = f"session:{session_id}:messages"
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            
            # Store message
            await client.rpush(messages_key, json.dumps(message_data))
            
            # Set TTL on the messages list
            await client.expire(messages_key, ttl_seconds)
            
            logger.info(f"Message stored in shared Redis for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store message in shared Redis for session {session_id}: {e}")
            return False
    
    async def get_messages(self, session_id: str) -> list:
        """
        Retrieve messages from the shared message Redis instance.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of message data
        """
        try:
            client = await self._get_message_client()
            messages_key = f"session:{session_id}:messages"
            
            messages = await client.lrange(messages_key, 0, -1)
            
            parsed_messages = []
            for msg_data in messages:
                try:
                    msg = json.loads(msg_data.decode('utf-8'))
                    parsed_messages.append(msg)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(f"Failed to parse message for session {session_id}: {e}")
                    continue
            
            return parsed_messages
            
        except Exception as e:
            logger.error(f"Failed to retrieve messages from shared Redis for session {session_id}: {e}")
            return []
    
    async def delete_messages(self, session_id: str) -> bool:
        """
        Delete messages for a session from the shared message Redis instance.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_message_client()
            messages_key = f"session:{session_id}:messages"
            
            result = await client.delete(messages_key)
            if result:
                logger.info(f"Messages deleted from shared Redis for session {session_id}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to delete messages from shared Redis for session {session_id}: {e}")
            return False

# Global Redis session manager instance
redis_session_manager: Optional[RedisSessionManager] = None

def get_redis_session_manager() -> RedisSessionManager:
    """Get the global Redis session manager instance."""
    global redis_session_manager
    if redis_session_manager is None:
        import os
        redis_url = os.environ.get("CHANNEL_REDIS_URL", "redis://localhost:6379/0")
        message_redis_url = os.environ.get("MESSAGE_REDIS_URL", redis_url)
        default_ttl = int(os.environ.get("REDIS_SESSION_TTL", "3600"))  # 1 hour default
        redis_session_manager = RedisSessionManager(redis_url, message_redis_url, default_ttl)
    return redis_session_manager
