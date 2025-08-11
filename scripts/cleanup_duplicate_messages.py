#!/usr/bin/env python3
"""
Redis message deduplication and cleanup utility.

This script performs maintenance operations on Redis message storage to remove
duplicate server response messages while preserving user messages. It ensures
data integrity and optimizes storage usage for the WebSocket service.

The deduplication process is essential for maintaining clean message history
and preventing storage bloat in production environments.
"""

import asyncio
import json
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.chat.redis_session import get_redis_session_manager

async def cleanup_duplicate_messages():
    """
    Perform comprehensive cleanup of duplicate messages in Redis storage.
    
    This function identifies and removes server response messages while
    preserving user messages to maintain clean message history. It processes
    all active sessions and provides detailed reporting of cleanup operations.
    
    The cleanup process is designed to be safe and non-destructive, ensuring
    data integrity while optimizing storage usage.
    """
    print("Initiating Redis message deduplication process...")
    
    try:
        # Initialize Redis connection manager
        redis_manager = get_redis_session_manager()
        client = await redis_manager._get_client()
        
        # Retrieve all session message keys for processing
        session_keys = await client.keys("session:*:messages")
        print(f"Discovered {len(session_keys)} active session message stores")
        
        total_cleaned = 0
        
        for session_key in session_keys:
            # Extract session identifier from Redis key
            session_id = session_key.decode('utf-8').replace('session:', '').replace(':messages', '')
            print(f"\nProcessing session: {session_id}")
            
            try:
                # Retrieve all messages for current session
                messages = await client.lrange(session_key, 0, -1)
                print(f"  Initial message count: {len(messages)}")
                
                if not messages:
                    print(f"  No messages found in session")
                    continue
                
                # Filter messages to remove server responses
                filtered_messages = []
                removed_count = 0
                
                for msg_data in messages:
                    try:
                        msg = json.loads(msg_data.decode('utf-8'))
                        content = msg.get('content', '')
                        
                        # Preserve user messages (isSent: True) and remove server responses
                        if msg.get('isSent', False) is True:
                            filtered_messages.append(msg_data)
                        else:
                            # Server response detected - mark for removal
                            removed_count += 1
                            print(f"    Removing server response: {content[:50]}...")
                            
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        print(f"    Warning: Failed to parse message format: {e}")
                        # Preserve unparseable messages to prevent data loss
                        filtered_messages.append(msg_data)
                
                if removed_count > 0:
                    # Perform atomic replacement of message list
                    await client.delete(session_key)
                    
                    if filtered_messages:
                        # Restore filtered messages to Redis
                        for msg_data in filtered_messages:
                            await client.rpush(session_key, msg_data)
                        
                        # Set appropriate TTL for message retention
                        await client.expire(session_key, redis_manager.default_ttl)
                    
                    print(f"  Cleanup completed: {removed_count} duplicate messages removed")
                    print(f"  Final message count: {len(filtered_messages)}")
                    total_cleaned += removed_count
                else:
                    print(f"  No duplicate messages found in session")
                
            except Exception as e:
                print(f"  Error processing session {session_id}: {e}")
                continue
        
        print(f"\nDeduplication process completed successfully")
        print(f"Total messages removed: {total_cleaned}")
        
        if total_cleaned > 0:
            print(f"\nNote: Browser refresh may be required to view updated message history")
        
    except Exception as e:
        print(f"Critical error during deduplication process: {e}")
        import traceback
        traceback.print_exc()

async def preview_duplicates():
    """
    Preview duplicate messages without performing cleanup operations.
    
    This function analyzes Redis message storage to identify potential
    duplicate messages and provides a summary without making any changes.
    It's useful for understanding the scope of cleanup operations before
    executing them.
    """
    print("Analyzing Redis message storage for duplicate detection...")
    
    try:
        # Initialize Redis connection
        redis_manager = get_redis_session_manager()
        client = await redis_manager._get_client()
        
        # Retrieve all session keys for analysis
        session_keys = await client.keys("session:*:messages")
        print(f"Found {len(session_keys)} session message stores to analyze")
        
        total_duplicates = 0
        total_messages = 0
        
        for session_key in session_keys:
            session_id = session_key.decode('utf-8').replace('session:', '').replace(':messages', '')
            print(f"\nAnalyzing session: {session_id}")
            
            try:
                # Retrieve messages for analysis
                messages = await client.lrange(session_key, 0, -1)
                total_messages += len(messages)
                
                if not messages:
                    print(f"  No messages found")
                    continue
                
                # Count potential duplicates
                duplicate_count = 0
                for msg_data in messages:
                    try:
                        msg = json.loads(msg_data.decode('utf-8'))
                        # Count server responses as potential duplicates
                        if not msg.get('isSent', False):
                            duplicate_count += 1
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Skip unparseable messages in analysis
                        continue
                
                total_duplicates += duplicate_count
                print(f"  Total messages: {len(messages)}")
                print(f"  Potential duplicates: {duplicate_count}")
                
            except Exception as e:
                print(f"  Error analyzing session {session_id}: {e}")
                continue
        
        print(f"\nAnalysis Summary:")
        print(f"  Total messages analyzed: {total_messages}")
        print(f"  Potential duplicates found: {total_duplicates}")
        print(f"  Duplicate percentage: {(total_duplicates/total_messages*100):.1f}%" if total_messages > 0 else "N/A")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """
    Main function to execute Redis message deduplication operations.
    
    This function provides a command-line interface for Redis message cleanup
    operations, including preview functionality and full cleanup execution.
    It ensures proper error handling and provides comprehensive reporting.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Redis message deduplication utility")
    parser.add_argument("--preview", action="store_true", 
                       help="Preview duplicates without performing cleanup")
    parser.add_argument("--confirm", action="store_true",
                       help="Confirm cleanup operation without prompting")
    
    args = parser.parse_args()
    
    print("Redis Message Deduplication Utility")
    print("=" * 50)
    
    if args.preview:
        # Execute preview analysis only
        await preview_duplicates()
    else:
        # Execute full cleanup process
        if not args.confirm:
            print("This operation will remove duplicate server response messages from Redis.")
            print("User messages will be preserved.")
            response = input("Proceed with cleanup? (y/N): ")
            if response.lower() != 'y':
                print("Cleanup operation cancelled")
                return
        
        print("Executing message deduplication process...")
        await cleanup_duplicate_messages()

if __name__ == "__main__":
    asyncio.run(main())
