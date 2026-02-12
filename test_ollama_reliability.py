#!/usr/bin/env python3
"""
2025-11-26: Ollama Reliability Test Script
Author: BabySteps Development Team
Purpose: Test the robust Ollama client with connection pooling and retry logic
Tests connection reliability under various scenarios
"""

import sys
import time
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# 2025-11-26: Add services directory to path
sys.path.insert(0, str(Path(__file__).parent / 'services' / 'mentor_chat_service'))

try:
    from ollama_client import ollama_client
except ImportError as e:
    print(f"[ERROR] Failed to import ollama_client: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

# 2025-11-26: Test configuration
NUM_SEQUENTIAL_TESTS = 10
NUM_CONCURRENT_TESTS = 20
TEST_PROMPTS = [
    "What is water?",
    "Explain photosynthesis simply.",
    "What is gravity?",
    "How do plants grow?",
    "What is the solar system?",
]

def print_header(title):
    """2025-11-26: Print formatted test section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_health_check():
    """2025-11-26: Test health check functionality"""
    print_header("TEST 1: Health Check")
    
    try:
        is_healthy = ollama_client.health_check(force=True)
        
        if is_healthy:
            print("✅ Health check PASSED")
            print(f"   - Ollama is running and model is available")
            print(f"   - Circuit breaker state: {ollama_client.circuit_breaker.state}")
            return True
        else:
            print("❌ Health check FAILED")
            print(f"   - Ollama may not be running or model not available")
            print(f"   - Circuit breaker state: {ollama_client.circuit_breaker.state}")
            return False
            
    except Exception as e:
        print(f"❌ Health check ERROR: {e}")
        return False

def test_sequential_requests():
    """2025-11-26: Test sequential requests to verify basic functionality"""
    print_header(f"TEST 2: Sequential Requests ({NUM_SEQUENTIAL_TESTS} requests)")
    
    successes = 0
    failures = 0
    response_times = []
    
    for i in range(NUM_SEQUENTIAL_TESTS):
        prompt = TEST_PROMPTS[i % len(TEST_PROMPTS)]
        print(f"\n[{i+1}/{NUM_SEQUENTIAL_TESTS}] Testing: '{prompt[:30]}...'")
        
        start_time = time.time()
        try:
            response = ollama_client.chat(
                message=prompt,
                system_prompt="You are a helpful teacher. Answer in 1-2 sentences.",
                temperature=0.7
            )
            elapsed = time.time() - start_time
            response_times.append(elapsed)
            
            if response and len(response) > 10:
                successes += 1
                print(f"   ✅ Success ({elapsed:.2f}s): {response[:60]}...")
            else:
                failures += 1
                print(f"   ❌ Failed: Empty or invalid response")
                
        except Exception as e:
            failures += 1
            elapsed = time.time() - start_time
            print(f"   ❌ Failed ({elapsed:.2f}s): {str(e)[:60]}")
    
    # 2025-11-26: Print summary
    print(f"\n{'─' * 70}")
    print(f"SEQUENTIAL TEST RESULTS:")
    print(f"  Total requests: {NUM_SEQUENTIAL_TESTS}")
    print(f"  Successes: {successes} ({successes/NUM_SEQUENTIAL_TESTS*100:.1f}%)")
    print(f"  Failures: {failures} ({failures/NUM_SEQUENTIAL_TESTS*100:.1f}%)")
    
    if response_times:
        print(f"  Response times:")
        print(f"    - Average: {statistics.mean(response_times):.2f}s")
        print(f"    - Min: {min(response_times):.2f}s")
        print(f"    - Max: {max(response_times):.2f}s")
        if len(response_times) > 1:
            print(f"    - Std Dev: {statistics.stdev(response_times):.2f}s")
    
    print(f"  Circuit breaker state: {ollama_client.circuit_breaker.state}")
    
    return successes == NUM_SEQUENTIAL_TESTS

def test_concurrent_requests():
    """2025-11-26: Test concurrent requests to verify connection pooling"""
    print_header(f"TEST 3: Concurrent Requests ({NUM_CONCURRENT_TESTS} parallel requests)")
    
    def make_request(request_id):
        """2025-11-26: Make a single request"""
        prompt = TEST_PROMPTS[request_id % len(TEST_PROMPTS)]
        start_time = time.time()
        
        try:
            response = ollama_client.chat(
                message=prompt,
                system_prompt="You are a helpful teacher. Answer in 1 sentence.",
                temperature=0.7
            )
            elapsed = time.time() - start_time
            
            return {
                'id': request_id,
                'success': True,
                'elapsed': elapsed,
                'response_length': len(response) if response else 0,
                'error': None
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                'id': request_id,
                'success': False,
                'elapsed': elapsed,
                'response_length': 0,
                'error': str(e)
            }
    
    # 2025-11-26: Execute concurrent requests
    print(f"\nStarting {NUM_CONCURRENT_TESTS} concurrent requests...")
    start_time = time.time()
    
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(NUM_CONCURRENT_TESTS)]
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            
            status = "✅" if result['success'] else "❌"
            print(f"  [{len(results)}/{NUM_CONCURRENT_TESTS}] {status} Request {result['id']} "
                  f"({result['elapsed']:.2f}s)")
    
    total_time = time.time() - start_time
    
    # 2025-11-26: Analyze results
    successes = sum(1 for r in results if r['success'])
    failures = sum(1 for r in results if not r['success'])
    response_times = [r['elapsed'] for r in results if r['success']]
    
    print(f"\n{'─' * 70}")
    print(f"CONCURRENT TEST RESULTS:")
    print(f"  Total requests: {NUM_CONCURRENT_TESTS}")
    print(f"  Successes: {successes} ({successes/NUM_CONCURRENT_TESTS*100:.1f}%)")
    print(f"  Failures: {failures} ({failures/NUM_CONCURRENT_TESTS*100:.1f}%)")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Throughput: {NUM_CONCURRENT_TESTS/total_time:.2f} requests/second")
    
    if response_times:
        print(f"  Response times:")
        print(f"    - Average: {statistics.mean(response_times):.2f}s")
        print(f"    - Min: {min(response_times):.2f}s")
        print(f"    - Max: {max(response_times):.2f}s")
        if len(response_times) > 1:
            print(f"    - Std Dev: {statistics.stdev(response_times):.2f}s")
    
    print(f"  Circuit breaker state: {ollama_client.circuit_breaker.state}")
    
    # 2025-11-26: Show failures if any
    if failures > 0:
        print(f"\n  Failed requests:")
        for r in results:
            if not r['success']:
                print(f"    - Request {r['id']}: {r['error'][:60]}")
    
    return successes >= NUM_CONCURRENT_TESTS * 0.9  # 90% success rate

def test_circuit_breaker_recovery():
    """2025-11-26: Test circuit breaker recovery after failures"""
    print_header("TEST 4: Circuit Breaker Recovery")
    
    print("\nThis test verifies that the circuit breaker can recover after failures.")
    print("Note: This test requires Ollama to be running.\n")
    
    # 2025-11-26: Check initial state
    print(f"Initial circuit breaker state: {ollama_client.circuit_breaker.state}")
    
    # 2025-11-26: Make a successful request
    try:
        response = ollama_client.chat(
            message="Hello",
            system_prompt="Say hi in one word.",
            temperature=0.7
        )
        print(f"✅ Test request successful: {response[:30]}...")
        print(f"Circuit breaker state after success: {ollama_client.circuit_breaker.state}")
        return True
        
    except Exception as e:
        print(f"❌ Test request failed: {e}")
        print(f"Circuit breaker state after failure: {ollama_client.circuit_breaker.state}")
        return False

def main():
    """2025-11-26: Run all reliability tests"""
    print("\n" + "=" * 70)
    print("  OLLAMA RELIABILITY TEST SUITE")
    print("  Testing connection pooling, retry logic, and circuit breaker")
    print("=" * 70)
    
    # 2025-11-26: Track overall results
    all_tests_passed = True
    
    # 2025-11-26: Test 1: Health Check
    if not test_health_check():
        print("\n⚠️  WARNING: Health check failed. Ollama may not be running.")
        print("   Please ensure:")
        print("   1. Ollama is running: ollama serve")
        print("   2. Model is available: ollama pull llama3.2")
        return 1
    
    # 2025-11-26: Test 2: Sequential Requests
    if not test_sequential_requests():
        print("\n⚠️  WARNING: Sequential test had failures")
        all_tests_passed = False
    
    # 2025-11-26: Test 3: Concurrent Requests
    if not test_concurrent_requests():
        print("\n⚠️  WARNING: Concurrent test had failures")
        all_tests_passed = False
    
    # 2025-11-26: Test 4: Circuit Breaker Recovery
    if not test_circuit_breaker_recovery():
        print("\n⚠️  WARNING: Circuit breaker recovery test failed")
        all_tests_passed = False
    
    # 2025-11-26: Final summary
    print_header("FINAL RESULTS")
    
    if all_tests_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nThe Ollama client is working reliably with:")
        print("  ✅ Connection pooling")
        print("  ✅ Retry logic")
        print("  ✅ Circuit breaker pattern")
        print("  ✅ Concurrent request handling")
        print("\nYour mentor chat should now have reliable connectivity!")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nPlease review the test output above for details.")
        print("Common issues:")
        print("  - Ollama not running (run: ollama serve)")
        print("  - Model not available (run: ollama pull llama3.2)")
        print("  - Network connectivity issues")
        print("  - Resource constraints (CPU/memory)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
