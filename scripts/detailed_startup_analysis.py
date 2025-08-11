#!/usr/bin/env python3
"""
Detailed Startup Time Analysis

This script breaks down startup time into the components:
1. Container creation & initialization time
2. Application boot time  
3. Dependency readiness time

Formula: Startup Time = (Container creation & initialization time) + (Application boot time) + (Dependency readiness time)
"""

import asyncio
import subprocess
import time
import json
from typing import Dict, Any

def measure_container_creation_time() -> float:
    """Measure container creation and initialization time."""
    print("Measuring container creation & initialization time...")
    
    start_time = time.perf_counter()
    
    try:
        # Stop the container first to ensure clean state
        subprocess.run(["docker", "compose", "-f", "docker/compose.yml", "stop", "app_green"], 
                      check=True, capture_output=True)
        
        # Start the container and measure until it's running
        result = subprocess.run(["docker", "compose", "-f", "docker/compose.yml", "up", "-d", "app_green"], 
                               check=True, capture_output=True, text=True)
        
        # Wait for container to be in "Up" state
        for i in range(50):  # 5 seconds max
            status_result = subprocess.run(
                ["docker", "ps", "--filter", "name=app_green", "--format", "{{.Status}}"],
                capture_output=True, text=True, timeout=1
            )
            if "Up" in status_result.stdout:
                container_time = time.perf_counter() - start_time
                print(f"✓ Container creation time: {container_time:.3f} seconds")
                return container_time
            time.sleep(0.1)
        
        print("✗ Container failed to start within timeout")
        return float('inf')
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Container creation failed: {e}")
        return float('inf')

def measure_application_boot_time() -> float:
    """Measure application boot time (from container running to app responding)."""
    print("Measuring application boot time...")
    
    start_time = time.perf_counter()
    
    try:
        # Wait for the application to respond to basic health check
        for i in range(100):  # 10 seconds max
            try:
                result = subprocess.run(
                    ["curl", "-f", "http://localhost/healthz"],
                    capture_output=True,
                    timeout=0.5
                )
                if result.returncode == 0:
                    boot_time = time.perf_counter() - start_time
                    print(f"✓ Application boot time: {boot_time:.3f} seconds")
                    return boot_time
            except subprocess.TimeoutExpired:
                pass
            time.sleep(0.1)
        
        print("✗ Application failed to boot within timeout")
        return float('inf')
        
    except Exception as e:
        print(f"✗ Application boot measurement failed: {e}")
        return float('inf')

def measure_dependency_readiness_time() -> float:
    """Measure dependency readiness time (from app responding to fully ready)."""
    print("Measuring dependency readiness time...")
    
    start_time = time.perf_counter()
    
    try:
        # Wait for the application to be fully ready (readyz endpoint)
        for i in range(100):  # 10 seconds max
            try:
                result = subprocess.run(
                    ["curl", "-f", "http://localhost/readyz"],
                    capture_output=True,
                    timeout=0.5
                )
                if result.returncode == 0:
                    readiness_time = time.perf_counter() - start_time
                    print(f"✓ Dependency readiness time: {readiness_time:.3f} seconds")
                    return readiness_time
            except subprocess.TimeoutExpired:
                pass
            time.sleep(0.1)
        
        print("✗ Dependencies failed to be ready within timeout")
        return float('inf')
        
    except Exception as e:
        print(f"✗ Dependency readiness measurement failed: {e}")
        return float('inf')

def measure_total_startup_time() -> float:
    """Measure total startup time (our current measurement)."""
    print("Measuring total startup time...")
    
    start_time = time.perf_counter()
    
    try:
        # Restart the container and measure until ready
        subprocess.run(["docker", "compose", "-f", "docker/compose.yml", "restart", "app_green"], 
                      check=True, capture_output=True)
        
        # Wait for readyz endpoint
        for i in range(200):  # 20 seconds max
            try:
                result = subprocess.run(
                    ["curl", "-f", "http://localhost/readyz"],
                    capture_output=True,
                    timeout=0.5
                )
                if result.returncode == 0:
                    total_time = time.perf_counter() - start_time
                    print(f"✓ Total startup time: {total_time:.3f} seconds")
                    return total_time
            except subprocess.TimeoutExpired:
                pass
            time.sleep(0.1)
        
        print("✗ Total startup failed within timeout")
        return float('inf')
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Total startup measurement failed: {e}")
        return float('inf')

def analyze_startup_components():
    """Analyze startup time components and validate the formula."""
    print("=" * 60)
    print("DETAILED STARTUP TIME ANALYSIS")
    print("=" * 60)
    print()
    
    # Measure each component
    container_time = measure_container_creation_time()
    print()
    
    boot_time = measure_application_boot_time()
    print()
    
    dependency_time = measure_dependency_readiness_time()
    print()
    
    # Measure total time
    total_time = measure_total_startup_time()
    print()
    
    # Calculate formula result
    formula_time = container_time + boot_time + dependency_time
    
    # Analysis
    print("=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)
    print()
    
    print("Formula Components:")
    print(f"  Container creation & initialization time: {container_time:.3f}s")
    print(f"  Application boot time:                    {boot_time:.3f}s")
    print(f"  Dependency readiness time:                {dependency_time:.3f}s")
    print(f"  ──────────────────────────────────────────────────")
    print(f"  Formula Total:                            {formula_time:.3f}s")
    print()
    
    print("Actual Measurement:")
    print(f"  Total startup time (measured):            {total_time:.3f}s")
    print()
    
    # Validation
    difference = abs(formula_time - total_time)
    percentage_diff = (difference / total_time * 100) if total_time > 0 else 0
    
    print("Validation:")
    print(f"  Difference:                               {difference:.3f}s ({percentage_diff:.1f}%)")
    
    if difference < 0.5:  # Within 0.5 seconds
        print("  ✅ Formula validation: PASS - Components match total")
    else:
        print("  ⚠️  Formula validation: PARTIAL - Some overlap or gaps detected")
    
    print()
    
    # Component breakdown
    print("Component Breakdown:")
    if container_time > 0:
        container_pct = (container_time / total_time * 100) if total_time > 0 else 0
        print(f"  Container creation: {container_pct:.1f}% of total startup time")
    
    if boot_time > 0:
        boot_pct = (boot_time / total_time * 100) if total_time > 0 else 0
        print(f"  Application boot:   {boot_pct:.1f}% of total startup time")
    
    if dependency_time > 0:
        dependency_pct = (dependency_time / total_time * 100) if total_time > 0 else 0
        print(f"  Dependencies:       {dependency_pct:.1f}% of total startup time")
    
    print()
    
    # Optimization insights
    print("Optimization Insights:")
    if container_time > boot_time and container_time > dependency_time:
        print("  🎯 Focus: Container creation is the biggest bottleneck")
    elif boot_time > container_time and boot_time > dependency_time:
        print("  🎯 Focus: Application boot time is the biggest bottleneck")
    elif dependency_time > container_time and dependency_time > boot_time:
        print("  🎯 Focus: Dependency readiness is the biggest bottleneck")
    
    return {
        "container_time": container_time,
        "boot_time": boot_time,
        "dependency_time": dependency_time,
        "total_time": total_time,
        "formula_time": formula_time,
        "difference": difference,
        "percentage_diff": percentage_diff
    }

if __name__ == "__main__":
    results = analyze_startup_components()
    
    # Save results for reference
    with open("startup_analysis_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("Results saved to startup_analysis_results.json")




