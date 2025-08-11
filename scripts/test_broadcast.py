#!/usr/bin/env python3
"""
Test script to demonstrate broadcast message functionality.
This script sends broadcast messages to all active WebSocket connections.
"""

import sys
import os
import time
import requests
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def test_broadcast_messages():
    """Test sending broadcast messages to all active connections."""
    
    print("🧪 Testing Broadcast Message Functionality")
    print("=" * 50)
    
    # Test different types of broadcast messages
    test_messages = [
        {
            "message": "System maintenance scheduled for tonight at 2 AM UTC",
            "title": "Maintenance Notice",
            "level": "info"
        },
        {
            "message": "Deployment in progress: Switching from blue to green environment",
            "title": "Deployment Started",
            "level": "warning"
        },
        {
            "message": "Traffic switched to green environment. New deployment is now active!",
            "title": "Deployment Complete",
            "level": "success"
        },
        {
            "message": "High error rate detected. Investigating...",
            "title": "System Alert",
            "level": "error"
        }
    ]
    
    for i, test_msg in enumerate(test_messages, 1):
        print(f"\n📡 Sending broadcast message {i}/{len(test_messages)}:")
        print(f"   Title: {test_msg['title']}")
        print(f"   Level: {test_msg['level']}")
        print(f"   Message: {test_msg['message']}")
        
        try:
            # Use Django management command to send broadcast
            import subprocess
            result = subprocess.run([
                'python', 'manage.py', 'broadcast_message',
                test_msg['message'],
                '--title', test_msg['title'],
                '--level', test_msg['level']
            ], capture_output=True, text=True, cwd='../app')
            
            if result.returncode == 0:
                print(f"   ✅ Success: {result.stdout.strip()}")
            else:
                print(f"   ❌ Error: {result.stderr.strip()}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Wait between messages
        time.sleep(2)
    
    print(f"\n🎉 Broadcast message test completed!")
    print("Check your WebSocket UI to see the broadcast messages appear.")

if __name__ == "__main__":
    test_broadcast_messages()
