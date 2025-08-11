#!/usr/bin/env python3
"""
Test Startup Optimization

This script tests the startup optimization improvements by measuring
the time it takes for the application to start and become ready.
"""

import asyncio
import subprocess
import time
import sys
from pathlib import Path

def test_startup_time():
    """Test the startup time of the optimized application."""
    print("Testing startup optimization...")
    print("=" * 50)
    
    # Build and start the application
    print("Building optimized Docker image...")
    try:
        subprocess.run([
            "docker", "compose", "-f", "docker/compose.yml", "build", "app_green"
        ], check=True, capture_output=True)
        print("✓ Docker image built successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Docker build failed: {e}")
        return False
    
    # Start the application
    print("\nStarting application...")
    try:
        subprocess.run([
            "docker", "compose", "-f", "docker/compose.yml", "up", "-d", "app_green"
        ], check=True, capture_output=True)
        print("✓ Application started")
    except subprocess.CalledProcessError as e:
        print(f"✗ Application start failed: {e}")
        return False
    
    # Measure startup time
    print("\nMeasuring startup time...")
    start_time = time.perf_counter()
    max_wait_time = 15  # Maximum wait time in seconds
    check_interval = 0.1  # Health check interval (very fast checks)
    
    for i in range(int(max_wait_time / check_interval)):
        try:
            # Check if service is responding to health endpoint
            result = subprocess.run(
                ["curl", "-f", "http://localhost/readyz"],
                capture_output=True,
                timeout=0.5
            )
            if result.returncode == 0:
                startup_time = time.perf_counter() - start_time
                print(f"✓ Service ready after {startup_time:.2f} seconds")
                
                # Test the optimization
                if startup_time < 3.0:
                    print("🎉 OPTIMIZATION SUCCESSFUL!")
                    print(f"   Target: < 3.0 seconds")
                    print(f"   Achieved: {startup_time:.2f} seconds")
                    print(f"   Improvement: {10.54 - startup_time:.2f} seconds faster")
                    return True
                else:
                    print("⚠ Optimization partially successful")
                    print(f"   Target: < 3.0 seconds")
                    print(f"   Achieved: {startup_time:.2f} seconds")
                    print(f"   Still needs improvement")
                    return False
        except subprocess.TimeoutExpired:
            pass
        
        time.sleep(check_interval)
    
    print("✗ Service failed to start within timeout period")
    return False

def cleanup():
    """Clean up the test environment."""
    print("\nCleaning up...")
    try:
        subprocess.run([
            "docker", "compose", "-f", "docker/compose.yml", "down"
        ], check=True, capture_output=True)
        print("✓ Cleanup completed")
    except subprocess.CalledProcessError as e:
        print(f"⚠ Cleanup warning: {e}")

def main():
    """Main test function."""
    print("Startup Optimization Test")
    print("=" * 50)
    
    try:
        success = test_startup_time()
        
        print("\n" + "=" * 50)
        print("TEST RESULTS")
        print("=" * 50)
        
        if success:
            print("✅ OPTIMIZATION TEST PASSED")
            print("   The application now starts in under 3 seconds!")
            return 0
        else:
            print("❌ OPTIMIZATION TEST FAILED")
            print("   The application still takes too long to start.")
            return 1
            
    finally:
        cleanup()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
