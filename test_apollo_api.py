#!/usr/bin/env python3
"""
Quick test for Apollo.io API key
"""

import os
import requests
import json

APOLLO_API_KEY = os.getenv('APOLLO_API_KEY')

if not APOLLO_API_KEY:
    print("❌ APOLLO_API_KEY not found!")
    print("Run: export APOLLO_API_KEY='your-key-here'")
    exit(1)

print(f"🔑 Testing API Key: {APOLLO_API_KEY[:10]}...\n")

# Test 1: Search for people
print("=" * 60)
print("TEST 1: People Search")
print("=" * 60)

headers = {
    'Content-Type': 'application/json',
    'X-Api-Key': APOLLO_API_KEY
}

payload = {
    "page": 1,
    "per_page": 5,
    "person_titles": ["IT Director", "CTO"],
    "person_locations": ["Dubai, United Arab Emirates"],
    "person_seniorities": ["director", "c_suite"]
}

try:
    response = requests.post(
        'https://api.apollo.io/v1/mixed_people/search',
        json=payload,
        headers=headers,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        people = data.get('people', [])
        pagination = data.get('pagination', {})
        
        print(f"✓ SUCCESS!")
        print(f"✓ Found {len(people)} people")
        print(f"✓ Total available: {pagination.get('total_entries', 0)}")
        
        if people:
            print("\n📋 Sample Results:")
            for person in people[:3]:
                print(f"  • {person.get('name')} - {person.get('title')}")
                print(f"    {person.get('organization', {}).get('name', 'N/A')}")
                print(f"    Email: {person.get('email', 'N/A')} ({person.get('email_status', 'N/A')})")
                print()
        
        print("=" * 60)
        print("✅ API KEY IS WORKING!")
        print("=" * 60)
        print("\nYou can now run the full scraper:")
        print("  python3 /tmp/apollo_linkedin_scraper.py")
        
    elif response.status_code == 401:
        print("✗ AUTHENTICATION FAILED")
        print("Your API key is invalid or expired.")
        print("\nGet a new key:")
        print("1. Login to: https://app.apollo.io/")
        print("2. Go to: Settings → Integrations → API")
        print("3. Create new API key")
        
    elif response.status_code == 429:
        print("✗ RATE LIMIT EXCEEDED")
        print("You've used all your credits or hit the rate limit.")
        print("\nCheck your credits:")
        print("  https://app.apollo.io/#/settings/credits")
        
    elif response.status_code == 422:
        print("✗ INVALID REQUEST")
        error = response.json().get('error', 'Unknown error')
        print(f"Error: {error}")
        
    else:
        print(f"✗ ERROR: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"✗ REQUEST FAILED: {e}")

print()
