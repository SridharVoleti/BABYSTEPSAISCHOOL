#!/usr/bin/env python3
"""
2025-11-16: Simple test for MentorChat endpoint
"""

import requests
import json

# Test the mentor chat endpoint
url = "http://localhost:8000/api/mentor/chat/"
data = {
    "message": "What is water?",
    "class_number": 1,
    "subject": "science"
}

print("Testing MentorChat endpoint...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")
print()

try:
    response = requests.post(
        url,
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        print("✅ SUCCESS!")
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ FAILED with status {response.status_code}")
        print("Response text:")
        print(response.text[:500])
        
except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection Error: {e}")
    print("Make sure Django is running: python manage.py runserver 8000")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
