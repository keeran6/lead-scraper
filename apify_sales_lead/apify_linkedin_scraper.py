#!/usr/bin/env python3
"""
Apify LinkedIn Lead Scraper
Scrapes LinkedIn profiles for UAE IT decision makers

Uses Apify's LinkedIn Profile Scraper actor
- 100 free actor runs/month
- Unlimited results
- No LinkedIn login required
"""

import os
import json
import sqlite3
import requests
import time
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# Apify Configuration
APIFY_API_TOKEN = "Token"
APIFY_USER_ID = "ID"

# Database and sync
DATABASE = "leads.db"
DAILY_TARGET = 50
GOOGLE_CREDS = "google-credentials.json"
SHEET_NAME = "UAE AI Hardware Leads"

# LinkedIn search URLs for UAE IT decision makers
LINKEDIN_SEARCH_URLS = [
    # IT Directors in UAE
    "https://www.linkedin.com/search/results/people/?keywords=IT%20Director%20UAE&origin=GLOBAL_SEARCH_HEADER",
    "https://www.linkedin.com/search/results/people/?keywords=IT%20Director%20Dubai&origin=GLOBAL_SEARCH_HEADER",
    "https://www.linkedin.com/search/results/people/?keywords=IT%20Director%20Sharjah&origin=GLOBAL_SEARCH_HEADER",
    
    # CTOs in UAE
    "https://www.linkedin.com/search/results/people/?keywords=CTO%20UAE&origin=GLOBAL_SEARCH_HEADER",
    "https://www.linkedin.com/search/results/people/?keywords=Chief%20Technology%20Officer%20Dubai&origin=GLOBAL_SEARCH_HEADER",
    
    # IT Managers
    "https://www.linkedin.com/search/results/people/?keywords=IT%20Manager%20UAE&origin=GLOBAL_SEARCH_HEADER",
    "https://www.linkedin.com/search/results/people/?keywords=Technology%20Manager%20Dubai&origin=GLOBAL_SEARCH_HEADER",
    
    # VPs and other senior roles
    "https://www.linkedin.com/search/results/people/?keywords=VP%20Technology%20UAE&origin=GLOBAL_SEARCH_HEADER",
    "https://www.linkedin.com/search/results/people/?keywords=Infrastructure%20Director%20Dubai&origin=GLOBAL_SEARCH_HEADER",
]

# Or use specific LinkedIn profile URLs if you have them
LINKEDIN_PROFILE_URLS = [
    # Add specific LinkedIn profile URLs here
    # "https://www.linkedin.com/in/profile-name/",
]


class ApifyLinkedInScraper:
    def __init__(self):
        self.api_token = APIFY_API_TOKEN
        self.user_id = APIFY_USER_ID
        self.base_url = "https://api.apify.com/v2"
        self.leads_collected = 0
        
        self._init_database()
        print(f"✓ Apify API configured")
        print(f"  User: {self.user_id}")
    
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                linkedin_url TEXT UNIQUE,
                name TEXT,
                first_name TEXT,
                last_name TEXT,
                title TEXT,
                headline TEXT,
                location TEXT,
                email TEXT,
                phone TEXT,
                company_name TEXT,
                company_website TEXT,
                company_linkedin TEXT,
                company_industry TEXT,
                connections TEXT,
                about TEXT,
                lead_score INTEGER,
                collected_date TEXT,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def run_linkedin_scraper_actor(self, search_urls=None, profile_urls=None, max_results=100):
        """
        Run Apify's LinkedIn Profile Scraper
        
        Actor: apify/linkedin-profile-scraper
        Docs: https://apify.com/apify/linkedin-profile-scraper
        """
        
        # Prepare input for the actor
        actor_input = {
            "startUrls": [],
            "maxResults": max_results,
            "proxyConfiguration": {
                "useApifyProxy": True
            }
        }
        
        # Add search URLs
        if search_urls:
            for url in search_urls:
                actor_input["startUrls"].append({"url": url})
        
        # Add specific profile URLs
        if profile_urls:
            for url in profile_urls:
                actor_input["startUrls"].append({"url": url})
        
        print(f"\n🚀 Starting Apify LinkedIn scraper...")
        print(f"   Targets: {len(actor_input['startUrls'])} URLs")
        print(f"   Max results: {max_results}")
        
        # Run the actor
        endpoint = f"{self.base_url}/acts/apify~linkedin-profile-scraper/runs?token={self.api_token}"
        
        try:
            response = requests.post(
                endpoint,
                json=actor_input,
                timeout=30
            )
            
            if response.status_code == 201:
                run_data = response.json()['data']
                run_id = run_data['id']
                
                print(f"✓ Actor started: {run_id}")
                print(f"   Status: {run_data['status']}")
                
                # Wait for completion
                return self._wait_for_run_completion(run_id)
            else:
                print(f"✗ Failed to start actor: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Error starting actor: {e}")
            return None
    
    def _wait_for_run_completion(self, run_id, max_wait=600):
        """Wait for actor run to complete"""
        endpoint = f"{self.base_url}/actor-runs/{run_id}?token={self.api_token}"
        
        start_time = time.time()
        print(f"⏳ Waiting for scraper to complete...")
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(endpoint, timeout=30)
                
                if response.status_code == 200:
                    run_data = response.json()['data']
                    status = run_data['status']
                    
                    if status == 'SUCCEEDED':
                        print(f"✓ Scraper completed successfully!")
                        dataset_id = run_data['defaultDatasetId']
                        return self._get_dataset_items(dataset_id)
                    
                    elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                        print(f"✗ Scraper failed: {status}")
                        return None
                    
                    else:
                        # Still running
                        elapsed = int(time.time() - start_time)
                        print(f"   Status: {status} (elapsed: {elapsed}s)", end='\r')
                        time.sleep(5)
                else:
                    print(f"✗ Error checking status: {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"✗ Error waiting for completion: {e}")
                return None
        
        print(f"✗ Timeout waiting for scraper (>{max_wait}s)")
        return None
    
    def _get_dataset_items(self, dataset_id):
        """Get items from dataset"""
        endpoint = f"{self.base_url}/datasets/{dataset_id}/items?token={self.api_token}&format=json"
        
        try:
            print(f"\n📥 Downloading results...")
            response = requests.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                items = response.json()
                print(f"✓ Downloaded {len(items)} profiles")
                return items
            else:
                print(f"✗ Error downloading results: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"✗ Error getting dataset: {e}")
            return []
    
    def extract_email_from_contact_info(self, contact_info):
        """Try to extract email from contact info"""
        if not contact_info:
            return None
        
        # Contact info sometimes has email in various fields
        for key in ['email', 'emailAddress', 'emails']:
            if key in contact_info and contact_info[key]:
                email = contact_info[key]
                if isinstance(email, list):
                    return email[0] if email else None
                return email
        
        return None
    
    def extract_phone_from_contact_info(self, contact_info):
        """Try to extract phone from contact info"""
        if not contact_info:
            return None
        
        for key in ['phone', 'phoneNumber', 'phoneNumbers']:
            if key in contact_info and contact_info[key]:
                phone = contact_info[key]
                if isinstance(phone, list):
                    return phone[0] if phone else None
                return phone
        
        return None
    
    def calculate_lead_score(self, profile):
        """Calculate lead quality score (0-100)"""
        score = 0
        
        # Job title relevance (40 points)
        title = (profile.get('title') or profile.get('headline') or '').lower()
        if any(x in title for x in ['cto', 'chief technology', 'chief information']):
            score += 40
        elif any(x in title for x in ['director', 'vp', 'vice president']):
            score += 30
        elif 'manager' in title:
            score += 20
        elif any(x in title for x in ['head', 'lead']):
            score += 15
        
        # Location match (20 points)
        location = (profile.get('location') or '').lower()
        if any(city in location for city in ['dubai', 'sharjah', 'rak', 'ras al khaimam', 'uae', 'emirates']):
            score += 20
        
        # Contact info (20 points)
        if profile.get('email'):
            score += 10
        if profile.get('phone'):
            score += 10
        
        # Profile completeness (20 points)
        if profile.get('about'):
            score += 5
        if profile.get('company_name'):
            score += 5
        if profile.get('connections'):
            connections = profile.get('connections', '')
            if '500+' in str(connections):
                score += 10
            elif int(''.join(filter(str.isdigit, str(connections))) or 0) > 200:
                score += 5
        
        return min(score, 100)
    
    def process_profile(self, profile_data):
        """Process a LinkedIn profile and extract lead data"""
        
        # Extract basic info
        linkedin_url = profile_data.get('url') or profile_data.get('profileUrl', '')
        
        if not linkedin_url:
            return None
        
        # Check for duplicate
        if self.is_duplicate(linkedin_url):
            return None
        
        # Extract name
        full_name = profile_data.get('fullName') or profile_data.get('name', '')
        first_name = profile_data.get('firstName', '')
        last_name = profile_data.get('lastName', '')
        
        if not first_name and full_name:
            parts = full_name.split()
            first_name = parts[0] if parts else ''
            last_name = parts[-1] if len(parts) > 1 else ''
        
        # Extract contact info
        contact_info = profile_data.get('contactInfo', {})
        email = self.extract_email_from_contact_info(contact_info)
        phone = self.extract_phone_from_contact_info(contact_info)
        
        # Extract company info
        current_position = profile_data.get('positions', [{}])[0] if profile_data.get('positions') else {}
        company_name = current_position.get('companyName', '')
        company_linkedin = current_position.get('companyUrl', '')
        
        # Build lead data
        lead = {
            'linkedin_url': linkedin_url,
            'name': full_name,
            'first_name': first_name,
            'last_name': last_name,
            'title': profile_data.get('title', ''),
            'headline': profile_data.get('headline', ''),
            'location': profile_data.get('location', ''),
            'email': email,
            'phone': phone,
            'company_name': company_name,
            'company_website': current_position.get('companyWebsite', ''),
            'company_linkedin': company_linkedin,
            'company_industry': profile_data.get('industry', ''),
            'connections': str(profile_data.get('connectionsCount', '')),
            'about': profile_data.get('summary', ''),
            'collected_date': datetime.now().isoformat()
        }
        
        # Calculate lead score
        lead['lead_score'] = self.calculate_lead_score(lead)
        
        # Add notes
        notes = []
        if email:
            notes.append("✓ Email found")
        if phone:
            notes.append("📞 Phone found")
        if lead['connections'] and '500+' in lead['connections']:
            notes.append("🌟 500+ connections")
        
        lead['notes'] = ' | '.join(notes)
        
        return lead
    
    def is_duplicate(self, linkedin_url):
        """Check if lead already exists"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM leads WHERE linkedin_url = ?', (linkedin_url,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def save_lead(self, lead):
        """Save lead to database"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO leads (
                    linkedin_url, name, first_name, last_name, title, headline,
                    location, email, phone, company_name, company_website,
                    company_linkedin, company_industry, connections, about,
                    lead_score, collected_date, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lead['linkedin_url'], lead['name'], lead['first_name'],
                lead['last_name'], lead['title'], lead['headline'],
                lead['location'], lead['email'], lead['phone'],
                lead['company_name'], lead['company_website'],
                lead['company_linkedin'], lead['company_industry'],
                lead['connections'], lead['about'], lead['lead_score'],
                lead['collected_date'], lead['notes']
            ))
            
            conn.commit()
            self.leads_collected += 1
            return True
            
        except sqlite3.IntegrityError:
            return False  # Duplicate
        except Exception as e:
            print(f"⚠️  Error saving lead: {e}")
            return False
        finally:
            conn.close()
    
    def sync_to_google_sheets(self):
        """Sync all leads to Google Sheets"""
        if not os.path.exists(GOOGLE_CREDS):
            print("⚠️  Google credentials not found. Skipping sync.")
            return False
        
        try:
            print("\n📊 Syncing to Google Sheets...")
            
            # Authenticate
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(GOOGLE_CREDS, scopes=scopes)
            client = gspread.authorize(creds)
            
            # Open or create sheet
            try:
                sheet = client.open(SHEET_NAME).sheet1
            except gspread.SpreadsheetNotFound:
                spreadsheet = client.create(SHEET_NAME)
                sheet = spreadsheet.sheet1
                spreadsheet.share('vikabotsystems@gmail.com', perm_type='user', role='writer')
            
            # Get all leads from database
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT name, title, company_name, location, email, phone,
                       linkedin_url, company_website, lead_score, connections,
                       collected_date, notes
                FROM leads
                ORDER BY lead_score DESC, collected_date DESC
            ''')
            leads = cursor.fetchall()
            conn.close()
            
            # Prepare data for sheets
            headers = [
                'Name', 'Title', 'Company', 'Location', 'Email', 'Phone',
                'LinkedIn', 'Website', 'Score', 'Connections', 'Collected', 'Notes'
            ]
            
            # Clear and update
            sheet.clear()
            sheet.update('A1', [headers] + [list(lead) for lead in leads])
            
            # Format header
            sheet.format('A1:L1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.8}
            })
            
            print(f"✓ Synced {len(leads)} leads to Google Sheets")
            print(f"  View at: {sheet.spreadsheet.url}")
            return True
            
        except Exception as e:
            print(f"⚠️  Google Sheets sync failed: {e}")
            return False
    
    def run_daily_collection(self):
        """Main collection routine"""
        print("\n" + "=" * 70)
        print("🚀 APIFY LINKEDIN LEAD COLLECTION STARTING")
        print("=" * 70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: {DAILY_TARGET} new leads")
        print()
        
        # Run Apify scraper
        profiles = self.run_linkedin_scraper_actor(
            search_urls=LINKEDIN_SEARCH_URLS[:3],  # Start with first 3 searches
            profile_urls=LINKEDIN_PROFILE_URLS,
            max_results=DAILY_TARGET + 20  # Get extra to account for duplicates
        )
        
        if not profiles:
            print("✗ No profiles returned from scraper")
            return 0
        
        print(f"\n📋 Processing {len(profiles)} profiles...")
        
        # Process each profile
        for i, profile_data in enumerate(profiles, 1):
            if self.leads_collected >= DAILY_TARGET:
                print(f"\n✓ Target reached: {self.leads_collected} leads")
                break
            
            lead = self.process_profile(profile_data)
            
            if lead:
                if self.save_lead(lead):
                    print(f"✓ [{self.leads_collected}/{DAILY_TARGET}] {lead['name']}")
                    print(f"  📧 {lead.get('email', 'N/A')} | 📍 {lead['location']} | ⭐ Score: {lead['lead_score']}")
                else:
                    print(f"⊝ Skipped: {lead['name']} (duplicate)")
            else:
                print(f"⊝ Skipped profile {i} (duplicate or invalid)")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 COLLECTION SUMMARY")
        print("=" * 70)
        print(f"✓ New leads collected: {self.leads_collected}")
        print(f"✓ Profiles processed: {len(profiles)}")
        print(f"✓ Database: {DATABASE}")
        
        # Sync to Google Sheets
        self.sync_to_google_sheets()
        
        print("\n✅ Collection complete!")
        return self.leads_collected


def main():
    """Main entry point"""
    try:
        scraper = ApifyLinkedInScraper()
        scraper.run_daily_collection()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
