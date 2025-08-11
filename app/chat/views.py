from __future__ import annotations

import os
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound

import json
from typing import Any, Dict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .redis_session import get_redis_session_manager
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time


logger = logging.getLogger(__name__)


def index_view(_request):
    # Serve the built UI index.html from STATIC_ROOT
    index_path = Path(os.environ.get("STATIC_ROOT", settings.STATIC_ROOT)) / "index.html"
    if index_path.exists():
        html_content = index_path.read_text(encoding="utf-8")
        
        # Get the COLOR environment variable (default to 'unknown')
        color = os.environ.get("COLOR", "unknown")
        
        # Inject a script tag to set the VITE_COLOR environment variable
        # This needs to be injected before the main script loads
        injection_script = f'<script>window.import_meta_env = {{ VITE_COLOR: "{color}" }};</script>'
        
        # Insert the script before the closing </head> tag
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", f"{injection_script}\n</head>")
        else:
            # Fallback: insert before the main script if no head tag
            html_content = html_content.replace('<script type="module" src="/src/main.tsx"></script>', 
                                              f'{injection_script}\n<script type="module" src="/src/main.tsx"></script>')
        
        return HttpResponse(html_content, content_type="text/html")
    return HttpResponseNotFound("UI is not built. Build the UI or run via Docker image.")


@csrf_exempt
@require_http_methods(["GET"])
async def session_info(request, session_id: str) -> JsonResponse:
    """Get session information from Redis."""
    try:
        redis_manager = get_redis_session_manager()
        session_info = await redis_manager.get_session_info(session_id)
        
        if session_info:
            return JsonResponse({
                "success": True,
                "session_id": session_id,
                "data": session_info
            })
        else:
            return JsonResponse({
                "success": False,
                "error": "Session not found",
                "session_id": session_id
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error getting session info for {session_id}: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e),
            "session_id": session_id
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
async def delete_session(request, session_id: str) -> JsonResponse:
    """Delete session from Redis."""
    try:
        redis_manager = get_redis_session_manager()
        success = await redis_manager.delete_session(session_id)
        
        if success:
            return JsonResponse({
                "success": True,
                "message": f"Session {session_id} deleted successfully"
            })
        else:
            return JsonResponse({
                "success": False,
                "error": "Session not found or already deleted",
                "session_id": session_id
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e),
            "session_id": session_id
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
async def extend_session(request, session_id: str) -> JsonResponse:
    """Extend session TTL in Redis."""
    try:
        data = json.loads(request.body)
        ttl = data.get("ttl")  # Optional TTL override
        
        redis_manager = get_redis_session_manager()
        success = await redis_manager.extend_session(session_id, ttl)
        
        if success:
            return JsonResponse({
                "success": True,
                "message": f"Session {session_id} TTL extended successfully"
            })
        else:
            return JsonResponse({
                "success": False,
                "error": "Session not found",
                "session_id": session_id
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error extending session {session_id}: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e),
            "session_id": session_id
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def redis_status(request) -> JsonResponse:
    """Get Redis session manager status."""
    import redis
    
    try:
        # Use synchronous Redis client
        redis_url = os.environ.get("CHANNEL_REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        
        # Test Redis connection
        r.ping()
        
        return JsonResponse({
            "success": True,
            "redis_connected": True,
            "redis_url": redis_url,
            "default_ttl": int(os.environ.get("REDIS_SESSION_TTL", "300"))
        })
        
    except Exception as e:
        logger.error(f"Redis status check failed: {e}")
        return JsonResponse({
            "success": False,
            "redis_connected": False,
            "error": str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
async def get_session_messages(request, session_id: str) -> JsonResponse:
    """Get messages for a specific session from Redis."""
    
    try:
        redis_manager = get_redis_session_manager()
        messages = await redis_manager.get_messages(session_id)
        
        # Parse messages
        parsed_messages = []
        for msg in messages:
            try:
                parsed_message = {
                    "content": msg.get("content", ""),
                    "timestamp": msg.get("timestamp", 0),
                    "isSent": msg.get("isSent", False),
                    "sessionId": session_id
                }
                
                # Add broadcast-specific fields if present
                if msg.get("isBroadcast"):
                    parsed_message["isBroadcast"] = True
                    parsed_message["broadcastLevel"] = msg.get("broadcastLevel", "info")
                
                parsed_messages.append(parsed_message)
            except Exception as e:
                logger.warning(f"Failed to parse message for session {session_id}: {e}")
                continue
        
        # Sort by timestamp (oldest first)
        parsed_messages.sort(key=lambda x: x["timestamp"])
        
        return JsonResponse({
            "success": True,
            "session_id": session_id,
            "messages": parsed_messages,
            "count": len(parsed_messages)
        })
        
    except Exception as e:
        logger.error(f"Error getting messages for session {session_id}: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e),
            "session_id": session_id
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
async def broadcast_message(request):
    """Send a broadcast message to all active WebSocket connections."""
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        title = data.get('title', 'System Message')
        level = data.get('level', 'info')
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'Message is required'
            }, status=400)
        
        # Validate level
        valid_levels = ['info', 'warning', 'error', 'success']
        if level not in valid_levels:
            return JsonResponse({
                'success': False,
                'error': f'Level must be one of: {", ".join(valid_levels)}'
            }, status=400)
        
        # Send broadcast message
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return JsonResponse({
                'success': False,
                'error': 'Channel layer not available'
            }, status=500)
        
        timestamp = int(time.time() * 1000)
        
        # Store broadcast message in Redis for all active sessions with Redis persistence
        try:
            redis_manager = get_redis_session_manager()
            
            # Get active sessions from WebSocket consumers (sessions with live connections)
            from app.chat.consumers import get_active_sessions
            active_session_ids = get_active_sessions()
            
            # Also get sessions from Redis for persistence (fallback)
            message_client = await redis_manager._get_message_client()
            session_client = await redis_manager._get_client()
            
            # Get sessions that already have message lists
            shared_session_keys = await message_client.keys("session:*:messages")
            env_session_keys = await session_client.keys("session:*:messages")
            existing_sessions = set()
            
            for key in shared_session_keys + env_session_keys:
                try:
                    session_id = key.decode('utf-8').split(':')[1]
                    existing_sessions.add(session_id)
                except (IndexError, UnicodeDecodeError):
                    continue
            
            # Also get all session keys (session data) to find active sessions
            all_session_keys = await session_client.keys("session:*")
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
                    
                    # Check if this broadcast message already exists in the session (in shared Redis)
                    existing_messages = await message_client.lrange(messages_key, 0, -1)
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
                        await message_client.rpush(messages_key, json.dumps(message_data))
                        
                        # Set TTL on the messages list (1 hour default)
                        default_ttl = int(os.environ.get("REDIS_SESSION_TTL", "3600"))
                        await message_client.expire(messages_key, default_ttl)
                        
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
        
        await channel_layer.group_send(
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
        await channel_layer.group_send(
            "broadcast",
            {
                "type": "server.new_messages_available",
                "timestamp": timestamp,
                "source": "broadcast_api"
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Broadcast message sent successfully',
            'data': {
                'message': message,
                'title': title,
                'level': level,
                'timestamp': timestamp,
                'sessions_updated': stored_count
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
