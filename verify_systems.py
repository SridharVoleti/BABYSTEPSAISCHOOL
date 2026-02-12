#!/usr/bin/env python3
"""
2025-11-22: System Verification Script
Author: BabySteps Development Team
Purpose: Verify TTS and Llama 3.2 connections
"""

import requests
import json
import time
import sys

def test_ollama_connection():
    """Test if Ollama is running and Llama 3.2 is available"""
    print("🔍 Testing Ollama Connection...")
    
    try:
        # Test Ollama service
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            print(f"✅ Ollama is running on port 11434")
            print(f"📋 Available models: {model_names}")
            
            # Check for llama3.2
            if any('llama3.2' in name for name in model_names):
                print("✅ Llama 3.2 model is available")
                
                # Test actual generation
                test_response = requests.post(
                    "http://127.0.0.1:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": "Hello, this is a test.",
                        "stream": False
                    },
                    timeout=10
                )
                
                if test_response.status_code == 200:
                    result = test_response.json()
                    print("✅ Llama 3.2 generation test successful")
                    print(f"📝 Sample response: {result.get('response', 'No response')[:100]}...")
                    return True
                else:
                    print("❌ Llama 3.2 generation test failed")
                    return False
            else:
                print("❌ Llama 3.2 model not found")
                print("💡 Run: ollama pull llama3.2")
                return False
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama on port 11434")
        print("💡 Run: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error testing Ollama: {e}")
        return False

def test_django_backend():
    """Test if Django backend is running and can connect to Ollama"""
    print("\n🔍 Testing Django Backend...")
    
    try:
        # Test health check endpoint
        response = requests.get("http://localhost:8000/api/mentor/health_check/", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Django backend is running on port 8000")
            print(f"📊 Backend status: {health_data.get('status', 'unknown')}")
            print(f"🔗 Ollama connected: {health_data.get('ollama_connected', False)}")
            
            if health_data.get('ollama_connected'):
                models = health_data.get('available_models', [])
                print(f"📋 Backend sees models: {models}")
                
                # Test actual chat endpoint
                chat_response = requests.post(
                    "http://localhost:8000/api/mentor/chat/",
                    json={
                        "message": "Hello, this is a test message.",
                        "class_number": 1
                    },
                    timeout=15
                )
                
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    if chat_data.get('success'):
                        print("✅ Django chat endpoint test successful")
                        print(f"📝 Sample response: {chat_data.get('text', 'No response')[:100]}...")
                        return True
                    else:
                        print(f"❌ Chat endpoint error: {chat_data.get('error', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ Chat endpoint returned status {chat_response.status_code}")
                    return False
            else:
                print("❌ Backend cannot connect to Ollama")
                return False
        else:
            print(f"❌ Django backend returned status {response.status_code}")
            print("💡 Run: python manage.py runserver")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django backend on port 8000")
        print("💡 Run: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error testing Django backend: {e}")
        return False

def test_frontend_tts():
    """Test TTS functionality (basic checks)"""
    print("\n🔍 Testing TTS Configuration...")
    
    # Check if TTS service file exists and has required components
    tts_file = "frontend/src/services/TTSService.js"
    tts_context = "frontend/src/contexts/TTSContext.js"
    
    try:
        with open(tts_file, 'r') as f:
            tts_content = f.read()
        
        with open(tts_context, 'r') as f:
            context_content = f.read()
        
        # Check for key components
        required_components = [
            "class TTSService",
            "speechSynthesis",
            "speak(",
            "loadVoices",
            "processQueue"
        ]
        
        missing_components = []
        for component in required_components:
            if component not in tts_content:
                missing_components.append(component)
        
        if not missing_components:
            print("✅ TTS Service has all required components")
        else:
            print(f"❌ TTS Service missing: {missing_components}")
            return False
        
        # Check context provider
        if "TTSProvider" in context_content and "useTTS" in context_content:
            print("✅ TTS Context Provider is configured")
        else:
            print("❌ TTS Context Provider is missing components")
            return False
        
        print("✅ TTS configuration looks complete")
        print("💡 Note: Actual TTS requires browser testing")
        return True
        
    except FileNotFoundError as e:
        print(f"❌ TTS file not found: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking TTS files: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 BabySteps Digital School - System Verification")
    print("=" * 50)
    
    results = {
        "Ollama": test_ollama_connection(),
        "Django Backend": test_django_backend(),
        "TTS Configuration": test_frontend_tts()
    }
    
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for system, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {system}: {'PASS' if status else 'FAIL'}")
        if not status:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL SYSTEMS VERIFIED - Ready to use!")
        print("\nNext steps:")
        print("1. Start the frontend: npm start")
        print("2. Open browser to http://localhost:3000")
        print("3. Test TTS and chat functionality")
    else:
        print("⚠️  SOME SYSTEMS NEED ATTENTION")
        print("\nPlease fix the failed systems before proceeding.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
