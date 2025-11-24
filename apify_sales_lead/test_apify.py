#!/usr/bin/env python3
"""
Test Apify API Connection
Quick test to verify your Apify credentials work
"""

import requests
import json

# Your Apify credentials
APIFY_API_TOKEN = "Provide_Your_lo8fSjkz0g"

print("=" * 60)
print("APIFY API TEST")
print("=" * 60)

# Test 1: Get user info
print("\n📋 TEST 1: Verify API Token")
print("-" * 60)

try:
    response = requests.get(
        f"https://api.apify.com/v2/users/me?token={APIFY_API_TOKEN}",
        timeout=10
    )
    
    if response.status_code == 200:
        user_data = response.json()['data']
        print(f"✓ API Token is VALID!")
        print(f"   User ID: {user_data.get('id')}")
        print(f"   Email: {user_data.get('email')}")
        print(f"   Plan: {user_data.get('plan', 'Free')}")
    else:
        print(f"✗ API Token is INVALID")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Test 2: Check available actors
print("\n📋 TEST 2: Check Available LinkedIn Actors")
print("-" * 60)

actors_to_check = [
    "dev_fusion/Linkedin-Profile-Scraper",
    "bebity/linkedin-premium-actor"
]

for actor in actors_to_check:
    try:
        response = requests.get(
            f"https://api.apify.com/v2/acts/{actor}?token={APIFY_API_TOKEN}",
            timeout=10
        )
        
        if response.status_code == 200:
            actor_data = response.json()['data']
            print(f"✓ {actor}")
            print(f"   Title: {actor_data.get('title')}")
            print(f"   Runs: {actor_data.get('stats', {}).get('totalRuns', 0)}")
        else:
            print(f"✗ {actor} - Not accessible")
            
    except Exception as e:
        print(f"✗ {actor} - Error: {e}")

# Test 3: List recent runs
print("\n📋 TEST 3: Your Recent Actor Runs")
print("-" * 60)

try:
    response = requests.get(
        f"https://api.apify.com/v2/actor-runs?token={APIFY_API_TOKEN}&limit=5",
        timeout=10
    )
    
    if response.status_code == 200:
        runs_data = response.json()['data']
        
        if not runs_data.get('items'):
            print("   No runs yet")
        else:
            for run in runs_data['items'][:5]:
                print(f"   • {run.get('actId')} - {run.get('status')} - {run.get('startedAt')}")
    else:
        print(f"✗ Could not fetch runs: {response.status_code}")
        
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("✅ API TEST COMPLETE!")
print("=" * 60)
print("\nYou can now run:")
print("  python3 /tmp/apify_linkedin_scraper.py")
print()
