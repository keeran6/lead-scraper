#!/usr/bin/env python3
"""
Apollo.io LinkedIn Lead Scraper
Professional B2B lead generation for UAE IT decision makers

Features:
- Search 50+ LinkedIn profiles/day
- Get verified emails & phone numbers
- Company data & enrichment
- Auto-sync to Google Sheets
- Duplicate detection
- Lead scoring

Apollo.io Free Trial: 50 credits (1 credit = 1 contact reveal)
Paid: $49/month for 1,200 credits
"""

import os
import json
import sqlite3
import requests
from datetime import datetime
import time
import gspread
from google.oauth2.service_account import Credentials

# Configuration
APOLLO_API_KEY = os.getenv('APOLLO_API_KEY')
DATABASE = "leads.db"
DAILY_TARGET = 50
GOOGLE_CREDS = "google-credentials.json"
SHEET_NAME = "UAE AI Hardware Leads"

# Search Filters for UAE IT Decision Makers
SEARCH_FILTERS = {
    "person_titles": [
        "IT Director",
        "CTO",
        "Chief Technology Officer",
        "VP Technology",
        "VP IT",
        "Technology Director",
        "IT Manager",
        "Infrastructure Manager",
        "Systems Director",
        "IT Procurement Manager"
    ],
    "person_locations": [
        "Dubai, United Arab Emirates",
        "Sharjah, United Arab Emirates",
        "Ras Al Khaimah, United Arab Emirates",
        "Abu Dhabi, United Arab Emirates",
        "Ajman, United Arab Emirates"
    ],
    "organization_num_employees_ranges": [
        "11,50",    # Small companies
        "51,200",   # Medium companies
        "201,500",  # Large companies
        "501,1000", # Enterprise
        "1001,10000" # Large enterprise
    ],
    "industries": [
        "Information Technology and Services",
        "Computer Software",
        "Telecommunications",
        "Financial Services",
        "Education Management",
        "Hospital & Health Care",
        "Retail",
        "Real Estate"
    ]
}


class ApolloLeadScraper:
    def __init__(self):
        if not APOLLO_API_KEY:
            raise Exception(
                "❌ APOLLO_API_KEY not found!\n"
                "Get your API key: https://app.apollo.io/#/settings/integrations/api\n"
                "Then run: export APOLLO_API_KEY='your-key-here'"
            )
        
        self.api_key = APOLLO_API_KEY
        self.base_url = "https://api.apollo.io/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Api-Key': self.api_key  # Apollo requires API key in header
        })
        
        self.leads_collected = 0
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                apollo_id TEXT UNIQUE,
                name TEXT,
                first_name TEXT,
                last_name TEXT,
                title TEXT,
                email TEXT,
                email_status TEXT,
                phone TEXT,
                mobile_phone TEXT,
                linkedin_url TEXT,
                company_name TEXT,
                company_website TEXT,
                company_linkedin TEXT,
                company_size TEXT,
                company_industry TEXT,
                location_city TEXT,
                location_state TEXT,
                location_country TEXT,
                lead_score INTEGER,
                contact_accuracy TEXT,
                collected_date TEXT,
                last_updated TEXT,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Database initialized")
    
    def search_people(self, page=1, per_page=25):
        """
        Search for people using Apollo.io People Search API
        
        API Docs: https://apolloio.github.io/apollo-api-docs/#search-for-people
        """
        endpoint = f"{self.base_url}/mixed_people/search"
        
        payload = {
            "page": page,
            "per_page": per_page,
            "person_titles": SEARCH_FILTERS["person_titles"],
            "person_locations": SEARCH_FILTERS["person_locations"],
            "organization_num_employees_ranges": SEARCH_FILTERS["organization_num_employees_ranges"],
            "person_seniorities": ["director", "vp", "c_suite", "manager"],
            "contact_email_status": ["verified", "guessed"],  # Only verified/guessed emails
            "q_organization_domains": None  # Search all companies
        }
        
        try:
            print(f"🔍 Searching Apollo.io (Page {page})...")
            response = self.session.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                people = data.get('people', [])
                pagination = data.get('pagination', {})
                
                print(f"✓ Found {len(people)} contacts (Total available: {pagination.get('total_entries', 0)})")
                return people, pagination
            
            elif response.status_code == 429:
                print("⚠️  Rate limit reached. Waiting 60 seconds...")
                time.sleep(60)
                return self.search_people(page, per_page)
            
            else:
                error_msg = response.json().get('error', 'Unknown error')
                print(f"✗ API Error ({response.status_code}): {error_msg}")
                return [], {}
                
        except Exception as e:
            print(f"✗ Request failed: {e}")
            return [], {}
    
    def enrich_person(self, person_id=None, email=None, reveal_email=False, reveal_phone=False):
        """
        Enrich person data (costs 1 credit per email/phone reveal)
        
        API Docs: https://apolloio.github.io/apollo-api-docs/#enrich-person
        """
        endpoint = f"{self.base_url}/people/match"
        
        payload = {
            "reveal_personal_emails": reveal_email,
            "reveal_phone_number": reveal_phone
        }
        
        if person_id:
            payload["id"] = person_id
        elif email:
            payload["email"] = email
        else:
            return None
        
        try:
            response = self.session.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('person', {})
            else:
                print(f"⚠️  Enrichment failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️  Enrichment error: {e}")
            return None
    
    def calculate_lead_score(self, person):
        """Calculate lead quality score (0-100)"""
        score = 0
        
        # Job title/seniority (35 points)
        title = person.get('title', '').lower()
        if any(x in title for x in ['cto', 'chief technology', 'chief information']):
            score += 35
        elif any(x in title for x in ['director', 'vp', 'vice president']):
            score += 30
        elif 'manager' in title:
            score += 20
        elif 'head' in title or 'lead' in title:
            score += 15
        
        # Contact info quality (30 points)
        email_status = person.get('email_status')
        if email_status == 'verified':
            score += 20
        elif email_status == 'guessed':
            score += 10
        
        if person.get('phone_numbers'):
            score += 10
        
        # Company size (20 points)
        org = person.get('organization', {})
        emp_count = org.get('estimated_num_employees', 0)
        if emp_count >= 1000:
            score += 20
        elif emp_count >= 200:
            score += 15
        elif emp_count >= 50:
            score += 10
        elif emp_count >= 10:
            score += 5
        
        # Location match (15 points)
        location = person.get('city', '').lower()
        if any(city in location for city in ['dubai', 'sharjah', 'rak', 'abu dhabi']):
            score += 15
        
        return min(score, 100)
    
    def extract_lead_data(self, person):
        """Extract and structure lead data from Apollo response"""
        org = person.get('organization', {}) or {}
        
        # Get phone numbers
        phone_numbers = person.get('phone_numbers', [])
        primary_phone = None
        mobile_phone = None
        
        for phone in phone_numbers:
            phone_str = phone.get('sanitized_number', '')
            if phone.get('type') == 'mobile':
                mobile_phone = phone_str
            elif not primary_phone:
                primary_phone = phone_str
        
        lead = {
            'apollo_id': person.get('id'),
            'name': person.get('name'),
            'first_name': person.get('first_name'),
            'last_name': person.get('last_name'),
            'title': person.get('title'),
            'email': person.get('email'),
            'email_status': person.get('email_status'),
            'phone': primary_phone,
            'mobile_phone': mobile_phone,
            'linkedin_url': person.get('linkedin_url'),
            'company_name': org.get('name'),
            'company_website': org.get('website_url'),
            'company_linkedin': org.get('linkedin_url'),
            'company_size': str(org.get('estimated_num_employees', '')),
            'company_industry': org.get('industry'),
            'location_city': person.get('city'),
            'location_state': person.get('state'),
            'location_country': person.get('country'),
            'contact_accuracy': person.get('email_confidence', ''),
            'collected_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        # Calculate lead score
        lead['lead_score'] = self.calculate_lead_score(person)
        
        # Add notes
        notes = []
        if person.get('email_status') == 'verified':
            notes.append("✓ Verified email")
        if mobile_phone:
            notes.append("📱 Mobile available")
        if org.get('estimated_num_employees', 0) >= 500:
            notes.append("🏢 Enterprise company")
        
        lead['notes'] = ' | '.join(notes)
        
        return lead
    
    def is_duplicate(self, apollo_id):
        """Check if lead already exists"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM leads WHERE apollo_id = ?', (apollo_id,))
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
                    apollo_id, name, first_name, last_name, title,
                    email, email_status, phone, mobile_phone, linkedin_url,
                    company_name, company_website, company_linkedin,
                    company_size, company_industry,
                    location_city, location_state, location_country,
                    lead_score, contact_accuracy, collected_date, last_updated, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lead['apollo_id'], lead['name'], lead['first_name'], lead['last_name'],
                lead['title'], lead['email'], lead['email_status'],
                lead['phone'], lead['mobile_phone'], lead['linkedin_url'],
                lead['company_name'], lead['company_website'], lead['company_linkedin'],
                lead['company_size'], lead['company_industry'],
                lead['location_city'], lead['location_state'], lead['location_country'],
                lead['lead_score'], lead['contact_accuracy'],
                lead['collected_date'], lead['last_updated'], lead['notes']
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
                # Share with your email
                spreadsheet.share('vikabotsystems@gmail.com', perm_type='user', role='writer')
            
            # Get all leads from database
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT name, title, company_name, location_city, email, phone,
                       linkedin_url, company_website, lead_score, email_status,
                       collected_date, notes
                FROM leads
                ORDER BY lead_score DESC, collected_date DESC
            ''')
            leads = cursor.fetchall()
            conn.close()
            
            # Prepare data for sheets
            headers = [
                'Name', 'Title', 'Company', 'Location', 'Email', 'Phone',
                'LinkedIn', 'Website', 'Score', 'Email Status', 'Collected', 'Notes'
            ]
            
            # Clear existing data and write new
            sheet.clear()
            sheet.update('A1', [headers] + [list(lead) for lead in leads])
            
            # Format header row
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
        print("🚀 APOLLO.IO LEAD COLLECTION STARTING")
        print("=" * 70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: {DAILY_TARGET} new leads")
        print(f"🔑 API Key: {self.api_key[:10]}...")
        print()
        
        page = 1
        total_processed = 0
        
        while self.leads_collected < DAILY_TARGET:
            # Search for people
            people, pagination = self.search_people(page=page, per_page=25)
            
            if not people:
                print("⚠️  No more results available")
                break
            
            # Process each person
            for person in people:
                if self.leads_collected >= DAILY_TARGET:
                    break
                
                apollo_id = person.get('id')
                name = person.get('name', 'Unknown')
                
                # Check duplicate
                if self.is_duplicate(apollo_id):
                    print(f"⊝ Skipped: {name} (duplicate)")
                    total_processed += 1
                    continue
                
                # Extract and save lead
                lead = self.extract_lead_data(person)
                
                if self.save_lead(lead):
                    print(f"✓ [{self.leads_collected}/{DAILY_TARGET}] {name} - {lead['title']}")
                    print(f"  📧 {lead['email']} | 📍 {lead['location_city']} | ⭐ Score: {lead['lead_score']}")
                else:
                    print(f"✗ Failed to save: {name}")
                
                total_processed += 1
                
                # Rate limiting: Wait 1 second between saves
                time.sleep(1)
            
            # Move to next page
            page += 1
            
            # Check if more pages available
            if pagination.get('page', 0) >= pagination.get('total_pages', 0):
                print("✓ Reached end of search results")
                break
            
            # Be polite - wait 2 seconds between pages
            print(f"⏳ Loading next page...")
            time.sleep(2)
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 COLLECTION SUMMARY")
        print("=" * 70)
        print(f"✓ New leads collected: {self.leads_collected}")
        print(f"✓ Total processed: {total_processed}")
        print(f"✓ Database: {DATABASE}")
        
        # Sync to Google Sheets
        self.sync_to_google_sheets()
        
        print("\n✅ Collection complete!")
        return self.leads_collected


def main():
    """Main entry point"""
    try:
        scraper = ApolloLeadScraper()
        scraper.run_daily_collection()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Setup Instructions:")
        print("1. Sign up at: https://app.apollo.io/")
        print("2. Get API key: Settings → Integrations → API")
        print("3. Configure: export APOLLO_API_KEY='your-key-here'")
        print("4. Run: python3 apollo_linkedin_scraper.py")


if __name__ == "__main__":
    main()
