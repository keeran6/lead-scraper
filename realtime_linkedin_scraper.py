#!/usr/bin/env python3
"""
Real-Time LinkedIn Lead Scraper
Collects 50 new IT decision makers daily from RAK/Sharjah
Auto-updates Google Sheets with only NEW leads

Methods:
1. Google Search → LinkedIn profiles (FREE)
2. LinkedIn Company Pages scraping (FREE)
3. Company Website scraping (FREE)
4. Email pattern generation (FREE)

Target: 50 new leads per day
Cost: $0/month
"""

import json
import os
import random
import re
import sqlite3
import time
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "google_credentials": "google-credentials.json",
    "google_sheet_name": "AI Hardware Sales Leads - RAK Sharjah",
    "database_path": "ai_hardware_leads.db",
    "daily_lead_target": 50,
    "search_delay": 5,  # seconds between searches
    "max_retries": 3
}

# Target job titles for IT hardware sales
TARGET_TITLES = [
    "IT Director UAE",
    "CTO Dubai",
    "CTO Sharjah", 
    "IT Manager RAK",
    "Technology Director UAE",
    "Infrastructure Manager Dubai",
    "CIO UAE",
    "VP IT Dubai",
    "Head of IT Sharjah",
    "IT Procurement Manager UAE"
]

# Target locations
TARGET_LOCATIONS = [
    "Ras Al Khaimah",
    "Sharjah",
    "Dubai",  # Include Dubai for more results
    "United Arab Emirates"
]

# ============================================================================
# LINKEDIN PROFILE FINDER (via Google Search)
# ============================================================================

class LinkedInProfileFinder:
    """
    Find LinkedIn profiles using Google Search
    FREE method - no LinkedIn API needed!
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
    
    def search_linkedin_profiles(self, job_title: str, location: str, limit: int = 10) -> List[str]:
        """
        Search Google for LinkedIn profiles
        
        Example query: site:linkedin.com/in "IT Director" "Sharjah" "UAE"
        """
        
        # Build Google search query
        query = f'site:linkedin.com/in "{job_title}" "{location}"'
        search_url = f'https://www.google.com/search?q={quote_plus(query)}&num={limit * 2}'
        
        print(f"  🔍 Searching: {job_title} in {location}")
        
        try:
            response = self.session.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract LinkedIn URLs
            linkedin_urls = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Clean Google redirect URLs
                if 'linkedin.com/in/' in href:
                    # Extract actual LinkedIn URL
                    if 'url?q=' in href:
                        linkedin_url = href.split('url?q=')[1].split('&')[0]
                    else:
                        linkedin_url = href
                    
                    # Clean and validate
                    if 'linkedin.com/in/' in linkedin_url and linkedin_url not in linkedin_urls:
                        # Remove query parameters
                        clean_url = linkedin_url.split('?')[0].split('#')[0]
                        linkedin_urls.append(clean_url)
            
            print(f"    Found {len(linkedin_urls)} LinkedIn profiles")
            return linkedin_urls[:limit]
            
        except Exception as e:
            print(f"    ⚠️  Search error: {e}")
            return []
    
    def scrape_linkedin_profile(self, profile_url: str) -> Optional[Dict]:
        """
        Scrape basic info from LinkedIn profile
        Note: This gets limited public data without login
        """
        
        try:
            response = self.session.get(profile_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract visible public data
            # Note: LinkedIn shows limited data to non-logged-in users
            
            profile_data = {
                'linkedin_url': profile_url,
                'name': '',
                'title': '',
                'company': '',
                'location': '',
                'scraped_at': datetime.now().isoformat()
            }
            
            # Try to extract from meta tags (public data)
            title_tag = soup.find('title')
            if title_tag:
                # Title usually contains: "Name | Title at Company | LinkedIn"
                title_text = title_tag.get_text()
                parts = title_text.split('|')
                if len(parts) >= 2:
                    profile_data['name'] = parts[0].strip()
                    profile_data['title'] = parts[1].strip()
            
            # Extract from meta description
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                desc = meta_desc.get('content')
                # Extract location from description
                if 'Location:' in desc or 'based in' in desc.lower():
                    # Try to extract location
                    pass
            
            return profile_data if profile_data['name'] else None
            
        except Exception as e:
            print(f"    ⚠️  Profile scrape error: {e}")
            return None

# ============================================================================
# COMPANY WEBSITE SCRAPER
# ============================================================================

class CompanyWebsiteScraper:
    """
    Scrape company websites for additional contact info
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36'
        }
    
    def find_company_website(self, company_name: str) -> Optional[str]:
        """
        Find company website using Google search
        """
        
        query = f'{company_name} UAE official website'
        search_url = f'https://www.google.com/search?q={quote_plus(query)}'
        
        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find first non-LinkedIn, non-social media result
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'url?q=' in href:
                    url = href.split('url?q=')[1].split('&')[0]
                    
                    # Skip social media and directories
                    skip_domains = ['linkedin', 'facebook', 'twitter', 'instagram', 'youtube', 
                                   'wikipedia', 'yellowpages', 'google']
                    
                    if not any(domain in url.lower() for domain in skip_domains):
                        if url.startswith('http'):
                            return url
            
            return None
            
        except Exception as e:
            print(f"    ⚠️  Website search error: {e}")
            return None
    
    def extract_contacts_from_website(self, website_url: str) -> Dict:
        """
        Extract emails and phones from company website
        """
        
        contacts = {
            'emails': [],
            'phones': []
        }
        
        try:
            response = requests.get(website_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            # Extract emails
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, text)
            
            # Filter valid emails
            valid_emails = []
            for email in emails:
                # Skip common false positives
                if not any(skip in email.lower() for skip in ['example.', 'test.', 'yourcompany', '.png', '.jpg']):
                    valid_emails.append(email)
            
            contacts['emails'] = list(set(valid_emails))[:5]  # Top 5 unique emails
            
            # Extract UAE phone numbers
            phone_patterns = [
                r'\+971[\s-]?\d{1,2}[\s-]?\d{3}[\s-]?\d{4}',
                r'00971[\s-]?\d{1,2}[\s-]?\d{3}[\s-]?\d{4}',
                r'0\d{1,2}[\s-]?\d{3}[\s-]?\d{4}'
            ]
            
            phones = []
            for pattern in phone_patterns:
                found = re.findall(pattern, text)
                phones.extend(found)
            
            contacts['phones'] = list(set(phones))[:3]  # Top 3 unique phones
            
            return contacts
            
        except Exception as e:
            print(f"    ⚠️  Contact extraction error: {e}")
            return contacts

# ============================================================================
# EMAIL GENERATOR
# ============================================================================

class EmailGenerator:
    """
    Generate possible email addresses using common patterns
    """
    
    @staticmethod
    def generate_emails(first_name: str, last_name: str, company_domain: str) -> List[str]:
        """
        Generate email options using common patterns
        """
        
        first = first_name.lower().strip()
        last = last_name.lower().strip()
        domain = company_domain.lower().strip()
        
        patterns = [
            f"{first}.{last}@{domain}",
            f"{first}@{domain}",
            f"{first}{last}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"{first}_{last}@{domain}",
            f"{last}.{first}@{domain}"
        ]
        
        return patterns
    
    @staticmethod
    def guess_company_domain(company_name: str) -> str:
        """
        Guess company domain from name
        """
        
        # Clean company name
        name = company_name.lower()
        name = re.sub(r'\b(llc|ltd|limited|inc|corporation|corp|group|holdings)\b', '', name)
        name = name.strip()
        
        # Common UAE company domains
        uae_companies = {
            'emirates': 'emirates.com',
            'etisalat': 'etisalat.ae',
            'du': 'du.ae',
            'adnoc': 'adnoc.ae',
            'enoc': 'enoc.com',
            'dewa': 'dewa.gov.ae',
            'sewa': 'sewa.gov.ae',
            'rakbank': 'rakbank.ae',
            'mashreq': 'mashreqbank.com',
            'emirates nbd': 'emiratesnbd.com'
        }
        
        # Check if it's a known company
        for key, domain in uae_companies.items():
            if key in name:
                return domain
        
        # Generate generic domain
        words = name.split()
        if words:
            base = words[0]
            return f"{base}.ae"  # UAE domain
        
        return "company.ae"

# ============================================================================
# LEAD SCORER
# ============================================================================

class LeadScorer:
    """
    Score leads based on multiple factors
    """
    
    @staticmethod
    def calculate_score(lead: Dict) -> int:
        """
        Calculate lead score 0-100
        """
        
        score = 0
        
        title = lead.get('title', '').lower()
        company = lead.get('company', '')
        location = lead.get('location', '').lower()
        
        # Job Title Score (40 points)
        if any(word in title for word in ['cto', 'cio', 'chief']):
            score += 40
        elif any(word in title for word in ['director', 'vp', 'head']):
            score += 30
        elif 'manager' in title:
            score += 20
        elif 'senior' in title:
            score += 15
        
        # Company Size (20 points) - estimate from name
        large_companies = ['emirates', 'etisalat', 'du', 'adnoc', 'dewa', 'sewa', 
                          'airport', 'bank', 'university', 'hospital']
        if any(comp in company.lower() for comp in large_companies):
            score += 20
        elif company:
            score += 10
        
        # Location Match (15 points)
        if 'sharjah' in location or 'ras al khaimah' in location or 'rak' in location:
            score += 15
        elif 'dubai' in location or 'uae' in location:
            score += 10
        
        # Has Contact Info (25 points)
        if lead.get('email_1'):
            score += 10
        if lead.get('phone'):
            score += 8
        if lead.get('linkedin_url'):
            score += 7
        
        return min(score, 100)
    
    @staticmethod
    def get_priority(score: int) -> str:
        """
        Get priority level from score
        """
        
        if score >= 90:
            return "Hot"
        elif score >= 80:
            return "High"
        elif score >= 70:
            return "Medium"
        else:
            return "Low"

# ============================================================================
# DATABASE (with duplicate detection)
# ============================================================================

class LeadDatabase:
    """
    SQLite database with duplicate detection
    """
    
    def __init__(self, db_path: str = CONFIG["database_path"]):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        """Create database schema"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_added TEXT,
                name TEXT NOT NULL,
                title TEXT,
                company TEXT,
                location TEXT,
                industry TEXT,
                company_size TEXT,
                linkedin_url TEXT UNIQUE,
                email_1 TEXT,
                email_2 TEXT,
                email_3 TEXT,
                phone TEXT,
                whatsapp TEXT,
                company_website TEXT,
                products_interest TEXT,
                lead_score INTEGER,
                priority TEXT,
                notes TEXT,
                next_action TEXT,
                status TEXT DEFAULT 'New',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_linkedin ON leads(linkedin_url)
        """)
        
        self.conn.commit()
    
    def is_duplicate(self, linkedin_url: str) -> bool:
        """
        Check if lead already exists
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads WHERE linkedin_url = ?", (linkedin_url,))
        count = cursor.fetchone()[0]
        return count > 0
    
    def insert_lead(self, lead: Dict) -> Optional[int]:
        """
        Insert lead (skip if duplicate)
        """
        
        # Check for duplicate
        if self.is_duplicate(lead.get('linkedin_url', '')):
            return None
        
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO leads (
                    date_added, name, title, company, location, industry, company_size,
                    linkedin_url, email_1, email_2, email_3, phone, whatsapp,
                    company_website, products_interest, lead_score, priority,
                    notes, next_action, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime('%Y-%m-%d'),
                lead.get('name', ''),
                lead.get('title', ''),
                lead.get('company', ''),
                lead.get('location', ''),
                lead.get('industry', ''),
                lead.get('company_size', ''),
                lead.get('linkedin_url', ''),
                lead.get('email_1', ''),
                lead.get('email_2', ''),
                lead.get('email_3', ''),
                lead.get('phone', ''),
                lead.get('whatsapp', ''),
                lead.get('company_website', ''),
                lead.get('products_interest', 'IT Hardware, Servers, Storage'),
                lead.get('lead_score', 0),
                lead.get('priority', 'Medium'),
                lead.get('notes', ''),
                lead.get('next_action', 'Send LinkedIn connection'),
                lead.get('status', 'New')
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def get_todays_leads(self) -> List[Dict]:
        """
        Get leads added today
        """
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT * FROM leads WHERE date_added = ? ORDER BY lead_score DESC", (today,))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_all_leads(self) -> List[Dict]:
        """
        Get all leads
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leads ORDER BY date_added DESC, lead_score DESC")
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

# ============================================================================
# GOOGLE SHEETS SYNC (only new leads)
# ============================================================================

class GoogleSheetsSync:
    """
    Sync only NEW leads to Google Sheets
    """
    
    def __init__(self, credentials_file: str, sheet_name: str):
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        self.client = gspread.authorize(creds)
        
        try:
            self.spreadsheet = self.client.open(sheet_name)
            self.sheet = self.spreadsheet.sheet1
        except gspread.SpreadsheetNotFound:
            self.spreadsheet = self.client.create(sheet_name)
            self.sheet = self.spreadsheet.sheet1
            self.spreadsheet.share('vikabotsystems@gmail.com', perm_type='user', role='writer')
        
        self.setup_headers()
    
    def setup_headers(self):
        """Create header row if not exists"""
        headers = [
            'Date Added', 'Name', 'Title', 'Company', 'Location', 'Industry',
            'Company Size', 'LinkedIn', 'Email Option 1', 'Email Option 2',
            'Email Option 3', 'Phone', 'WhatsApp', 'Website', 'Products Interest',
            'Lead Score', 'Priority', 'Status', 'Next Action', 'Notes'
        ]
        
        try:
            existing = self.sheet.row_values(1)
            if not existing or existing[0] != 'Date Added':
                self.sheet.insert_row(headers, 1)
                self.sheet.format('A1:T1', {
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.4, 'green': 0.5, 'blue': 0.9}
                })
        except:
            self.sheet.insert_row(headers, 1)
    
    def append_new_leads(self, leads: List[Dict]):
        """
        Append only NEW leads to sheet
        """
        
        if not leads:
            return
        
        rows = []
        for lead in leads:
            row = [
                lead.get('date_added', ''),
                lead.get('name', ''),
                lead.get('title', ''),
                lead.get('company', ''),
                lead.get('location', ''),
                lead.get('industry', ''),
                lead.get('company_size', ''),
                lead.get('linkedin_url', ''),
                lead.get('email_1', ''),
                lead.get('email_2', ''),
                lead.get('email_3', ''),
                lead.get('phone', ''),
                lead.get('whatsapp', ''),
                lead.get('company_website', ''),
                lead.get('products_interest', ''),
                lead.get('lead_score', 0),
                lead.get('priority', ''),
                lead.get('status', ''),
                lead.get('next_action', ''),
                lead.get('notes', '')
            ]
            rows.append(row)
        
        if rows:
            self.sheet.append_rows(rows, value_input_option='RAW')
            print(f"✓ Added {len(rows)} new leads to Google Sheets")

# ============================================================================
# MAIN SCRAPER ORCHESTRATOR
# ============================================================================

class DailyLeadCollector:
    """
    Main orchestrator - collects 50 new leads daily
    """
    
    def __init__(self):
        self.db = LeadDatabase()
        self.linkedin_finder = LinkedInProfileFinder()
        self.website_scraper = CompanyWebsiteScraper()
        self.email_gen = EmailGenerator()
        self.scorer = LeadScorer()
        
        if GSHEETS_AVAILABLE and os.path.exists(CONFIG["google_credentials"]):
            self.sheets = GoogleSheetsSync(
                CONFIG["google_credentials"],
                CONFIG["google_sheet_name"]
            )
        else:
            self.sheets = None
    
    def collect_daily_leads(self, target: int = 50):
        """
        Collect target number of NEW leads
        """
        
        print("=" * 70)
        print("🚀 DAILY LEAD COLLECTION - RAK/SHARJAH/DUBAI")
        print("=" * 70)
        print(f"Target: {target} NEW leads")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()
        
        new_leads = []
        attempts = 0
        max_attempts = target * 3  # Try 3x to get enough leads
        
        # Rotate through job titles and locations
        searches = []
        for title in TARGET_TITLES:
            for location in TARGET_LOCATIONS[:2]:  # RAK and Sharjah priority
                searches.append((title, location))
        
        # Shuffle for variety
        random.shuffle(searches)
        
        for title, location in searches:
            if len(new_leads) >= target:
                break
            
            if attempts >= max_attempts:
                print(f"\n⚠️  Reached maximum attempts ({max_attempts})")
                break
            
            # Find LinkedIn profiles
            linkedin_urls = self.linkedin_finder.search_linkedin_profiles(
                title, location, limit=5
            )
            
            # Process each profile
            for url in linkedin_urls:
                if len(new_leads) >= target:
                    break
                
                attempts += 1
                
                # Check if already exists
                if self.db.is_duplicate(url):
                    print(f"    ⏭️  Skipping duplicate: {url}")
                    continue
                
                # Enrich lead data
                lead_data = self.enrich_lead(url)
                
                if lead_data and lead_data.get('name'):
                    # Insert to database
                    lead_id = self.db.insert_lead(lead_data)
                    
                    if lead_id:
                        new_leads.append(lead_data)
                        print(f"    ✓ Added: {lead_data.get('name')} ({lead_data.get('lead_score')})")
                
                # Delay between requests
                time.sleep(random.uniform(3, 7))
        
        print(f"\n{'=' * 70}")
        print(f"📊 COLLECTION COMPLETE")
        print(f"{'=' * 70}")
        print(f"New leads collected: {len(new_leads)}")
        print(f"Target: {target}")
        print(f"Success rate: {len(new_leads)/target*100:.1f}%")
        
        # Sync to Google Sheets
        if self.sheets and new_leads:
            print(f"\n📊 Syncing to Google Sheets...")
            try:
                self.sheets.append_new_leads(new_leads)
                print(f"  View at: {self.sheets.spreadsheet.url}")
            except Exception as e:
                print(f"  ⚠️  Sync failed: {e}")
        
        # Generate summary
        self.print_summary(new_leads)
        
        return new_leads
    
    def enrich_lead(self, linkedin_url: str) -> Optional[Dict]:
        """
        Enrich lead with all available data
        """
        
        lead = {
            'linkedin_url': linkedin_url,
            'name': '',
            'title': '',
            'company': '',
            'location': '',
            'industry': '',
            'company_size': '',
            'email_1': '',
            'email_2': '',
            'email_3': '',
            'phone': '',
            'whatsapp': '',
            'company_website': '',
            'products_interest': 'IT Hardware, Servers, GPU Systems, Storage, AMC',
            'lead_score': 0,
            'priority': 'Medium',
            'notes': '',
            'next_action': 'Send LinkedIn connection request',
            'status': 'New'
        }
        
        # Extract from LinkedIn profile (limited public data)
        profile_data = self.linkedin_finder.scrape_linkedin_profile(linkedin_url)
        
        if profile_data:
            lead.update(profile_data)
        
        # Parse name for email generation
        if lead['name']:
            name_parts = lead['name'].split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[-1]
                
                # Generate emails if we have company
                if lead['company']:
                    domain = self.email_gen.guess_company_domain(lead['company'])
                    emails = self.email_gen.generate_emails(first_name, last_name, domain)
                    
                    lead['email_1'] = emails[0] if len(emails) > 0 else ''
                    lead['email_2'] = emails[1] if len(emails) > 1 else ''
                    lead['email_3'] = emails[2] if len(emails) > 2 else ''
        
        # Find company website
        if lead['company']:
            website = self.website_scraper.find_company_website(lead['company'])
            if website:
                lead['company_website'] = website
                
                # Extract contacts from website
                contacts = self.website_scraper.extract_contacts_from_website(website)
                
                if contacts['phones']:
                    lead['phone'] = contacts['phones'][0]
                    # Check if it's a mobile (has '5' in UAE mobile numbers)
                    if '5' in lead['phone']:
                        lead['whatsapp'] = lead['phone']
        
        # Calculate lead score
        lead['lead_score'] = self.scorer.calculate_score(lead)
        lead['priority'] = self.scorer.get_priority(lead['lead_score'])
        
        return lead if lead['name'] else None
    
    def print_summary(self, new_leads: List[Dict]):
        """
        Print summary of collected leads
        """
        
        if not new_leads:
            print("\n⚠️  No new leads collected")
            return
        
        print(f"\n{'=' * 70}")
        print("🌟 TOP 10 NEW LEADS")
        print(f"{'=' * 70}")
        
        # Sort by score
        sorted_leads = sorted(new_leads, key=lambda x: x.get('lead_score', 0), reverse=True)
        
        for i, lead in enumerate(sorted_leads[:10], 1):
            print(f"\n{i}. {lead.get('name')} - Score: {lead.get('lead_score')}")
            print(f"   {lead.get('title')} at {lead.get('company')}")
            print(f"   📍 {lead.get('location')}")
            if lead.get('email_1'):
                print(f"   📧 {lead.get('email_1')}")
            if lead.get('phone'):
                print(f"   📞 {lead.get('phone')}")
            print(f"   🔗 {lead.get('linkedin_url')}")
        
        print(f"\n{'=' * 70}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main execution - run daily to collect 50 new leads
    """
    
    collector = DailyLeadCollector()
    
    # Collect 50 new leads
    new_leads = collector.collect_daily_leads(target=CONFIG["daily_lead_target"])
    
    print(f"\n✅ Daily collection complete!")
    print(f"💾 Database: {CONFIG['database_path']}")
    print(f"📊 Google Sheets: {CONFIG['google_sheet_name']}")
    print(f"\n🎯 Ready to start outreach with {len(new_leads)} new leads!")

if __name__ == "__main__":
    main()
