from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time
import json
import os
import redis
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send a broadcast message to all active WebSocket connections and store in shared Redis'

    def add_arguments(self, parser):
        parser.add_argument(
            'message',
            type=str,
            help='The message to broadcast'
        )
        parser.add_argument(
            '--title',
            type=str,
            default='System Message',
            help='Title for the broadcast message'
        )
        parser.add_argument(
            '--level',
            type=str,
            choices=['info', 'warning', 'error', 'success'],
            default='info',
            help='Message level (info, warning, error, success)'
        )

    def handle(self, *args, **options):
        channel_layer = get_channel_layer()
        if channel_layer is None:
            self.stdout.write(
                self.style.ERROR('Channel layer not available')
            )
            return

        message = options['message']
        title = options['title']
        level = options['level']
        timestamp = int(time.time() * 1000)

        # Store broadcast message in shared Redis for all active sessions
        try:
            # Get shared Redis URL from environment
            message_redis_url = os.environ.get("MESSAGE_REDIS_URL", "redis://localhost:6379/1")
            r = redis.from_url(message_redis_url)
            
            # Get active sessions from WebSocket consumers (sessions with live connections)
            from app.chat.consumers import get_active_sessions
            active_session_ids = get_active_sessions()
            
            # Get all active sessions (both with and without message lists)
            # First, get sessions that already have message lists
            existing_session_keys = r.keys("session:*:messages")
            existing_sessions = set()
            
            for key in existing_session_keys:
                try:
                    session_id = key.decode('utf-8').split(':')[1]
                    existing_sessions.add(session_id)
                except (IndexError, UnicodeDecodeError):
                    continue
            
            # Also get all session keys (session data) to find active sessions
            all_session_keys = r.keys("session:*")
            all_sessions = set()
            
            for key in all_session_keys:
                try:
                    # Skip message lists, only get session data keys
                    if not key.decode('utf-8').endswith(':messages'):
                        session_id = key.decode('utf-8').split(':')[1]
                        all_sessions.add(session_id)
                except (IndexError, UnicodeDecodeError):
                    continue
            
            # Combine both sets to get all sessions in Redis
            all_redis_sessions = existing_sessions.union(all_sessions)
            
            # Prioritize active WebSocket sessions, but include all Redis sessions for persistence
            target_sessions = active_session_ids.union(all_redis_sessions)
            
            broadcast_content = f"[{title}] {message}"
            message_data = {
                "content": broadcast_content,
                "timestamp": timestamp,
                "isSent": False,  # This was sent by the server
                "isBroadcast": True,
                "broadcastLevel": level,
                "broadcastId": f"broadcast_{timestamp}_{hash(broadcast_content) % 10000}"  # Unique broadcast ID
            }
            
            stored_count = 0
            active_stored_count = 0
            
            for session_id in target_sessions:
                try:
                    messages_key = f"session:{session_id}:messages"
                    
                    # Check if this broadcast message already exists in the session
                    existing_messages = r.lrange(messages_key, 0, -1)
                    is_duplicate = False
                    
                    # Check for duplicate broadcast using broadcast ID
                    broadcast_id = message_data.get("broadcastId")
                    
                    for existing_msg in existing_messages:
                        try:
                            existing_data = json.loads(existing_msg.decode('utf-8'))
                            # Check for same broadcast ID
                            if (existing_data.get("broadcastId") == broadcast_id and 
                                existing_data.get("isBroadcast")):
                                is_duplicate = True
                                break
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
                    
                    if not is_duplicate:
                        # Store broadcast message for this session in shared Redis
                        r.rpush(messages_key, json.dumps(message_data))
                        
                        # Set TTL on the messages list (1 hour default)
                        default_ttl = int(os.environ.get("REDIS_SESSION_TTL", "3600"))
                        r.expire(messages_key, default_ttl)
                        
                        stored_count += 1
                        
                        # Track if this was an active session
                        if session_id in active_session_ids:
                            active_stored_count += 1
                            
                        logger.info(f"Broadcast message stored in shared Redis for session {session_id}")
                    else:
                        logger.info(f"Broadcast message already exists in shared Redis for session {session_id}, skipping")
                        
                except Exception as e:
                    logger.error(f"Failed to store broadcast message for session {session_id}: {e}")
                    continue
            
            logger.info(f"Broadcast message stored in shared Redis for {stored_count} total sessions ({active_stored_count} active)")
            
        except Exception as e:
            logger.error(f"Failed to store broadcast messages in shared Redis: {e}")

        # Send broadcast message to all connected clients
        async_to_sync(channel_layer.group_send)(
            "broadcast",
            {
                "type": "server.broadcast",
                "message": message,
                "title": title,
                "level": level,
                "timestamp": timestamp
            }
        )

        # Send notifications to all connected clients that new messages are available
        async_to_sync(channel_layer.group_send)(
            "broadcast",
            {
                "type": "server.new_messages_available",
                "timestamp": timestamp,
                "source": "management_command"
            }
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Broadcast message sent: "{message}" (level: {level}) - stored in {stored_count} sessions'
            )
        )
