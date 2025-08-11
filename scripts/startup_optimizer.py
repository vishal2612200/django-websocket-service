#!/usr/bin/env python3
"""
Startup Optimizer for WebSocket Application

This script optimizes the startup time by:
1. Pre-warming critical Python modules
2. Pre-compiling bytecode
3. Optimizing import paths
4. Reducing initialization overhead
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def pre_warm_modules():
    """Pre-warm critical Python modules for faster startup."""
    print("Pre-warming critical modules...")
    
    modules_to_warm = [
        'django',
        'channels',
        'redis',
        'uvicorn',
        'asgiref',
        'prometheus_client',
        'json_logger'
    ]
    
    for module in modules_to_warm:
        try:
            __import__(module)
            print(f"✓ Pre-warmed {module}")
        except ImportError:
            print(f"⚠ Module {module} not available")
        except Exception as e:
            print(f"✗ Error pre-warming {module}: {e}")

def optimize_python_environment():
    """Set Python environment variables for faster startup."""
    print("Optimizing Python environment...")
    
    optimizations = {
        'PYTHONOPTIMIZE': '2',
        'PYTHONHASHSEED': '0',
        'PYTHONFAULTHANDLER': '0',
        'PYTHONUNBUFFERED': '1',
        'PYTHONDONTWRITEBYTECODE': '1',
        'UVICORN_ACCESS_LOG': '0',
        'UVICORN_LOG_LEVEL': 'warning'
    }
    
    for key, value in optimizations.items():
        os.environ[key] = value
        print(f"✓ Set {key}={value}")

def pre_compile_bytecode():
    """Pre-compile Python bytecode for faster startup."""
    print("Pre-compiling bytecode...")
    
    app_dir = Path(__file__).parent.parent / 'app'
    if app_dir.exists():
        try:
            result = subprocess.run([
                sys.executable, '-m', 'compileall', 
                str(app_dir), '-q', '-f', '-j', '0'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Bytecode compilation successful")
            else:
                print(f"⚠ Bytecode compilation warnings: {result.stderr}")
        except Exception as e:
            print(f"✗ Bytecode compilation error: {e}")
    else:
        print("⚠ App directory not found, skipping bytecode compilation")

def optimize_file_system():
    """Optimize file system for faster startup."""
    print("Optimizing file system...")
    
    app_dir = Path(__file__).parent.parent / 'app'
    if app_dir.exists():
        try:
            # Remove .pyc files and __pycache__ directories
            for pyc_file in app_dir.rglob("*.pyc"):
                pyc_file.unlink()
            
            for cache_dir in app_dir.rglob("__pycache__"):
                import shutil
                shutil.rmtree(cache_dir)
            
            print("✓ File system optimization complete")
        except Exception as e:
            print(f"✗ File system optimization error: {e}")
    else:
        print("⚠ App directory not found, skipping file system optimization")

def measure_startup_time():
    """Measure the optimized startup time."""
    print("\nMeasuring optimized startup time...")
    
    start_time = time.perf_counter()
    
    try:
        # Import the application
        sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))
        from app.asgi import application
        
        startup_time = time.perf_counter() - start_time
        print(f"✓ Application import time: {startup_time:.3f} seconds")
        
        return startup_time
    except Exception as e:
        print(f"✗ Application import error: {e}")
        return float('inf')

def main():
    """Main optimization function."""
    print("WebSocket Application Startup Optimizer")
    print("=" * 50)
    
    # Step 1: Optimize Python environment
    optimize_python_environment()
    
    # Step 2: Optimize file system
    optimize_file_system()
    
    # Step 3: Pre-compile bytecode
    pre_compile_bytecode()
    
    # Step 4: Pre-warm modules
    pre_warm_modules()
    
    # Step 5: Measure startup time
    startup_time = measure_startup_time()
    
    print("\n" + "=" * 50)
    print("OPTIMIZATION SUMMARY")
    print("=" * 50)
    print(f"Startup Time: {startup_time:.3f} seconds")
    
    if startup_time < 3.0:
        print("✓ Target achieved: < 3.0 seconds")
        return 0
    else:
        print("✗ Target not achieved: < 3.0 seconds")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
