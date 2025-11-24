#!/usr/bin/env python3
"""
Apify LinkedIn Scraper - Multi-Actor Version
Uses multiple Apify actors for comprehensive data collection

Available Actors:
1. apify/linkedin-profile-scraper - Basic profile scraping
2. apify/linkedin-company-scraper - Company page scraping  
3. mishamo/linkedin-search-scraper - Search results scraping
"""

import os
import json
import sqlite3
import requests
import time
from datetime import datetime

# Apify Configuration
APIFY_API_TOKEN = "apify_api_kEcpZp1e8KYW22TXE7iM55lo8fSjkz0gGBiI"
APIFY_USER_ID = "MzYxLPBnQJUlBL9P8"
DATABASE = "leads.db"

# Choose which actor to use
ACTOR_OPTIONS = {
    "profile_scraper": "apify/linkedin-profile-scraper",
    "search_scraper": "mishamo/linkedin-search-scraper",
    "company_scraper": "apify/linkedin-company-scraper"
}


class ApifyMultiScraper:
    def __init__(self):
        self.api_token = APIFY_API_TOKEN
        self.base_url = "https://api.apify.com/v2"
        self._init_database()
    
    def _init_database(self):
        """Initialize database"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                linkedin_url TEXT UNIQUE,
                name TEXT,
                title TEXT,
                company TEXT,
                location TEXT,
                email TEXT,
                phone TEXT,
                lead_score INTEGER,
                collected_date TEXT,
                raw_data TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def run_actor(self, actor_name, actor_input, timeout=600):
        """Generic method to run any Apify actor"""
        
        endpoint = f"{self.base_url}/acts/{actor_name}/runs?token={self.api_token}"
        
        print(f"\n🚀 Running actor: {actor_name}")
        print(f"   Input: {json.dumps(actor_input, indent=2)[:200]}...")
        
        try:
            # Start actor
            response = requests.post(endpoint, json=actor_input, timeout=30)
            
            if response.status_code != 201:
                print(f"✗ Failed to start actor: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
            
            run_data = response.json()['data']
            run_id = run_data['id']
            print(f"✓ Actor started: {run_id}")
            
            # Wait for completion
            return self._wait_and_get_results(run_id, timeout)
            
        except Exception as e:
            print(f"✗ Error running actor: {e}")
            return None
    
    def _wait_and_get_results(self, run_id, timeout):
        """Wait for run and get results"""
        endpoint = f"{self.base_url}/actor-runs/{run_id}?token={self.api_token}"
        
        start_time = time.time()
        print(f"⏳ Waiting for completion...")
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(endpoint, timeout=30)
                
                if response.status_code == 200:
                    run_data = response.json()['data']
                    status = run_data['status']
                    
                    if status == 'SUCCEEDED':
                        print(f"✓ Completed!")
                        dataset_id = run_data['defaultDatasetId']
                        return self._get_dataset(dataset_id)
                    
                    elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                        print(f"✗ Failed: {status}")
                        return None
                    
                    else:
                        elapsed = int(time.time() - start_time)
                        print(f"   Status: {status} ({elapsed}s)", end='\r')
                        time.sleep(5)
                        
            except Exception as e:
                print(f"✗ Error: {e}")
                return None
        
        print(f"✗ Timeout")
        return None
    
    def _get_dataset(self, dataset_id):
        """Get dataset items"""
        endpoint = f"{self.base_url}/datasets/{dataset_id}/items?token={self.api_token}&format=json"
        
        try:
            response = requests.get(endpoint, timeout=30)
            if response.status_code == 200:
                items = response.json()
                print(f"✓ Downloaded {len(items)} results")
                return items
            else:
                print(f"✗ Error downloading: {response.status_code}")
                return []
        except Exception as e:
            print(f"✗ Error: {e}")
            return []
    
    def scrape_linkedin_search(self, search_query, max_results=50):
        """
        Use mishamo/linkedin-search-scraper
        Better for search results
        """
        
        actor_input = {
            "searchQuery": search_query,
            "maxResults": max_results,
            "filters": {
                "network": ["F", "S", "O"],  # 1st, 2nd, 3rd+ connections
                "industry": [],
                "pastCompany": [],
                "profileLanguage": [],
                "serviceCategory": [],
                "geoUrn": []
            }
        }
        
        results = self.run_actor("mishamo/linkedin-search-scraper", actor_input)
        return results if results else []
    
    def scrape_linkedin_profiles(self, profile_urls, max_results=50):
        """
        Use apify/linkedin-profile-scraper  
        Best for detailed profile data
        """
        
        actor_input = {
            "startUrls": [{"url": url} for url in profile_urls],
            "maxResults": max_results,
            "proxyConfiguration": {
                "useApifyProxy": True
            }
        }
        
        results = self.run_actor("apify/linkedin-profile-scraper", actor_input)
        return results if results else []
    
    def process_and_save_leads(self, results):
        """Process results and save to database"""
        saved = 0
        
        for item in results:
            # Extract common fields
            lead = {
                'linkedin_url': item.get('url') or item.get('profileUrl', ''),
                'name': item.get('name') or item.get('fullName', ''),
                'title': item.get('title') or item.get('headline', ''),
                'company': item.get('company') or (item.get('positions', [{}])[0].get('companyName', '') if item.get('positions') else ''),
                'location': item.get('location', ''),
                'email': None,  # Usually not available
                'phone': None,  # Usually not available
                'lead_score': 50,  # Default score
                'collected_date': datetime.now().isoformat(),
                'raw_data': json.dumps(item)
            }
            
            if self._save_lead(lead):
                saved += 1
                print(f"✓ Saved: {lead['name']}")
        
        print(f"\n✓ Saved {saved} new leads")
        return saved
    
    def _save_lead(self, lead):
        """Save lead to database"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO leads (
                    linkedin_url, name, title, company, location,
                    email, phone, lead_score, collected_date, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lead['linkedin_url'], lead['name'], lead['title'],
                lead['company'], lead['location'], lead['email'],
                lead['phone'], lead['lead_score'], lead['collected_date'],
                lead['raw_data']
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()


def main():
    """Example usage"""
    
    print("=" * 70)
    print("APIFY MULTI-ACTOR LINKEDIN SCRAPER")
    print("=" * 70)
    
    scraper = ApifyMultiScraper()
    
    # Option 1: Search for people
    print("\n📋 METHOD 1: LinkedIn Search")
    print("   Searching for: IT Directors in UAE")
    
    results = scraper.scrape_linkedin_search(
        search_query="IT Director UAE",
        max_results=25
    )
    
    if results:
        scraper.process_and_save_leads(results)
    
    # Option 2: Scrape specific profiles
    # print("\n📋 METHOD 2: Profile Scraping")
    # profile_urls = [
    #     "https://www.linkedin.com/in/example1/",
    #     "https://www.linkedin.com/in/example2/",
    # ]
    # results = scraper.scrape_linkedin_profiles(profile_urls)
    # if results:
    #     scraper.process_and_save_leads(results)
    
    print("\n" + "=" * 70)
    print("✅ SCRAPING COMPLETE")
    print(f"📁 Database: {DATABASE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
