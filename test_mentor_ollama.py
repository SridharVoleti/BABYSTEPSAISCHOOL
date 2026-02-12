#!/usr/bin/env python3
"""
2025-11-16: Test script to verify MentorChat → Django → Ollama connectivity
Author: BabySteps Development Team
Purpose: Diagnose and verify the complete request flow
"""

import requests
import json
import os

# Configuration
DJANGO_URL = "http://localhost:8000/api/mentor/chat"
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

def test_ollama_direct():
    """Test direct connection to Ollama"""
    print("\n=== Testing Direct Ollama Connection ===")
    try:
        # Test if Ollama is running
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running at {OLLAMA_URL}")
            print(f"📦 Available models: {[m['name'] for m in models]}")
            
            # Check if llama3.2 is available
            if any(OLLAMA_MODEL in m['name'] for m in models):
                print(f"✅ Model '{OLLAMA_MODEL}' is available")
                return True
            else:
                print(f"❌ Model '{OLLAMA_MODEL}' not found. Run: ollama pull {OLLAMA_MODEL}")
                return False
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {OLLAMA_URL}")
        print("   Make sure Ollama is running: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_ollama_generate():
    """Test Ollama generation"""
    print("\n=== Testing Ollama Generation ===")
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": "Say 'Hello from Ollama!' in one sentence.",
                "stream": False
            },
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Ollama generated response:")
            print(f"   {result.get('response', 'No response')[:100]}...")
            return True
        else:
            print(f"❌ Ollama generate failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_django_backend():
    """Test Django mentor chat endpoint"""
    print("\n=== Testing Django Backend ===")
    try:
        # Test if Django is running
        response = requests.get("http://localhost:8000/api/", timeout=5)
        if response.status_code in [200, 404]:  # 404 is ok if root not defined
            print("✅ Django server is running at http://localhost:8000")
        else:
            print(f"⚠️  Django returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django at http://localhost:8000")
        print("   Make sure Django is running: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test mentor chat endpoint
    try:
        response = requests.post(
            DJANGO_URL,
            json={
                "message": "What is photosynthesis?",
                "class_number": 1,
                "subject": "science"
            },
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Django → Ollama connection working!")
                print(f"   Teacher: {data.get('teacher', 'Unknown')}")
                print(f"   Response: {data.get('text', '')[:100]}...")
                return True
            else:
                print(f"❌ Backend returned error: {data.get('error')}")
                return False
        elif response.status_code == 502:
            print(f"❌ Bad Gateway (502): Ollama connection failed")
            print(f"   Error: {response.json().get('error', 'Unknown')}")
            return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>60s)")
        print("   Ollama might be slow or not responding")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("MentorChat → Django → Ollama Connectivity Test")
    print("=" * 60)
    
    # Test 1: Ollama direct connection
    ollama_ok = test_ollama_direct()
    
    # Test 2: Ollama generation
    if ollama_ok:
        ollama_gen_ok = test_ollama_generate()
    else:
        ollama_gen_ok = False
        print("\n⏭️  Skipping Ollama generation test (Ollama not available)")
    
    # Test 3: Django backend
    django_ok = test_django_backend()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Ollama Connection:  {'✅ PASS' if ollama_ok else '❌ FAIL'}")
    print(f"Ollama Generation:  {'✅ PASS' if ollama_gen_ok else '❌ FAIL'}")
    print(f"Django → Ollama:    {'✅ PASS' if django_ok else '❌ FAIL'}")
    
    if ollama_ok and ollama_gen_ok and django_ok:
        print("\n🎉 All tests passed! MentorChat should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        if not ollama_ok:
            print("  1. Start Ollama: ollama serve")
            print(f"  2. Pull model: ollama pull {OLLAMA_MODEL}")
        if not django_ok:
            print("  3. Start Django: python manage.py runserver")
            print("  4. Check OLLAMA_BASE_URL environment variable")

if __name__ == "__main__":
    main()
