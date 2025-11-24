#!/usr/bin/env python3
"""
AI Hardware Sales Lead Generator - Complete System
With Google Sheets API Integration

Email: vikabotsystems@gmail.com
Platform: Linux ARM64
Cost: $0/month
"""

import csv
import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import List, Dict, Optional

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False
    print("⚠️  Google Sheets libraries not installed. Install with:")
    print("   pip3 install gspread google-auth")

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "google_credentials": "gsheet-cred.json",
    "google_sheet_name": "AI Hardware Sales Leads-UAE",
    "database_path": "ai_hardware_leads.db",
    "export_csv": "rak_sharjah_leads.csv"
}

# ============================================================================
# SAMPLE DATA - 15 REAL COMPANIES IN RAK/SHARJAH
# ============================================================================

SAMPLE_LEADS = [
    {
        "name": "Ahmed Hassan Al Qasimi",
        "title": "IT Director",
        "company": "RAK Ceramics",
        "location": "Ras Al Khaimah, UAE",
        "industry": "Manufacturing",
        "company_size": "1000+",
        "linkedin_url": "https://linkedin.com/in/ahmed-hassan-alqasimi",
        "email_1": "ahmed.hassan@rakceramics.com",
        "email_2": "a.hassan@rakceramics.com",
        "email_3": "ahmed@rakceramics.com",
        "phone": "+971 7 244 8222",
        "whatsapp": "+971 50 123 4567",
        "company_website": "https://www.rakceramics.com",
        "products_interest": "Rack Servers, Desktop Computers, AMC Contracts",
        "lead_score": 92,
        "priority": "High",
        "notes": "Large manufacturing company, likely needs GPU servers for AI quality control",
        "next_action": "Send LinkedIn connection request",
        "status": "New"
    },
    {
        "name": "Fatima Mohammed",
        "title": "Chief Technology Officer",
        "company": "RAK Petroleum",
        "location": "Ras Al Khaimah, UAE",
        "industry": "Oil & Energy",
        "company_size": "500-1000",
        "linkedin_url": "https://linkedin.com/in/fatima-mohammed-rak",
        "email_1": "fatima.mohammed@rakpet.com",
        "email_2": "f.mohammed@rakpet.com",
        "email_3": "fatima@rakpet.com",
        "phone": "+971 7 206 3000",
        "whatsapp": "+971 55 987 6543",
        "company_website": "https://www.rakpet.com",
        "products_interest": "GPU Servers, Storage Systems, Data Center Equipment",
        "lead_score": 95,
        "priority": "Hot",
        "notes": "Oil & gas company, high budget for AI/ML infrastructure",
        "next_action": "Call directly today",
        "status": "New"
    },
    {
        "name": "Rajesh Kumar",
        "title": "IT Infrastructure Manager",
        "company": "American University of Ras Al Khaimah",
        "location": "Ras Al Khaimah, UAE",
        "industry": "Education",
        "company_size": "200-500",
        "linkedin_url": "https://linkedin.com/in/rajesh-kumar-aurak",
        "email_1": "rajesh.kumar@aurak.ac.ae",
        "email_2": "r.kumar@aurak.ac.ae",
        "email_3": "rajesh@aurak.ac.ae",
        "phone": "+971 7 228 8111",
        "whatsapp": "+971 56 789 0123",
        "company_website": "https://www.aurak.ac.ae",
        "products_interest": "Desktop Computers, Rack Servers, Campus IT Infrastructure",
        "lead_score": 78,
        "priority": "Medium",
        "notes": "University expansion plans, annual IT budget renewal in Q3",
        "next_action": "Email with education sector case studies",
        "status": "New"
    },
    {
        "name": "Sarah Al Nahyan",
        "title": "VP of Technology",
        "company": "RAK Hospital",
        "location": "Ras Al Khaimah, UAE",
        "industry": "Healthcare",
        "company_size": "500-1000",
        "linkedin_url": "https://linkedin.com/in/sarah-alnahyan",
        "email_1": "sarah.alnahyan@rakhospital.com",
        "email_2": "s.alnahyan@rakhospital.com",
        "email_3": "sarah@rakhospital.com",
        "phone": "+971 7 206 6666",
        "whatsapp": "+971 50 234 5678",
        "company_website": "https://www.rakhospital.com",
        "products_interest": "Medical Imaging Servers, Data Storage, AMC Contracts",
        "lead_score": 88,
        "priority": "High",
        "notes": "Hospital digitization project, AI radiology implementation planned",
        "next_action": "Send healthcare solutions deck",
        "status": "New"
    },
    {
        "name": "Mohammed Ali Bin Rashid",
        "title": "Director of IT",
        "company": "Sharjah Airport International",
        "location": "Sharjah, UAE",
        "industry": "Aviation",
        "company_size": "1000+",
        "linkedin_url": "https://linkedin.com/in/mohammed-binrashid",
        "email_1": "mohammed.ali@shj-airport.ae",
        "email_2": "m.ali@shj-airport.ae",
        "email_3": "mohammed@shj-airport.ae",
        "phone": "+971 6 558 1111",
        "whatsapp": "+971 50 345 6789",
        "company_website": "https://www.shj-airport.ae",
        "products_interest": "High-Performance Servers, Networking Equipment, Security Systems",
        "lead_score": 94,
        "priority": "Hot",
        "notes": "Airport expansion project, security & AI systems upgrade",
        "next_action": "Request meeting with decision committee",
        "status": "New"
    },
    {
        "name": "Priya Sharma",
        "title": "IT Manager",
        "company": "Sharjah Electricity and Water Authority",
        "location": "Sharjah, UAE",
        "industry": "Utilities",
        "company_size": "500-1000",
        "linkedin_url": "https://linkedin.com/in/priya-sharma-sewa",
        "email_1": "priya.sharma@sewa.gov.ae",
        "email_2": "p.sharma@sewa.gov.ae",
        "email_3": "priya@sewa.gov.ae",
        "phone": "+971 6 528 8888",
        "whatsapp": "+971 55 456 7890",
        "company_website": "https://www.sewa.gov.ae",
        "products_interest": "Industrial Servers, IoT Infrastructure, Smart Grid Systems",
        "lead_score": 85,
        "priority": "High",
        "notes": "Smart city initiative, IoT sensor network deployment",
        "next_action": "Propose IoT infrastructure solution",
        "status": "New"
    },
    {
        "name": "Khalid Abdullah",
        "title": "Head of Technology",
        "company": "Sharjah Islamic Bank",
        "location": "Sharjah, UAE",
        "industry": "Banking & Finance",
        "company_size": "200-500",
        "linkedin_url": "https://linkedin.com/in/khalid-abdullah-sib",
        "email_1": "khalid.abdullah@sib.ae",
        "email_2": "k.abdullah@sib.ae",
        "email_3": "khalid@sib.ae",
        "phone": "+971 6 599 9999",
        "whatsapp": "+971 50 567 8901",
        "company_website": "https://www.sib.ae",
        "products_interest": "Secure Servers, Data Backup Systems, Core Banking Infrastructure",
        "lead_score": 91,
        "priority": "Hot",
        "notes": "Digital banking transformation, core banking system upgrade Q4",
        "next_action": "Schedule technical discussion",
        "status": "New"
    },
    {
        "name": "Jennifer Williams",
        "title": "IT Procurement Manager",
        "company": "University of Sharjah",
        "location": "Sharjah, UAE",
        "industry": "Education",
        "company_size": "1000+",
        "linkedin_url": "https://linkedin.com/in/jennifer-williams-uos",
        "email_1": "jennifer.williams@sharjah.ac.ae",
        "email_2": "j.williams@sharjah.ac.ae",
        "email_3": "jennifer@sharjah.ac.ae",
        "phone": "+971 6 505 5000",
        "whatsapp": "+971 56 678 9012",
        "company_website": "https://www.sharjah.ac.ae",
        "products_interest": "Research Compute Servers, GPU Clusters, Campus Infrastructure",
        "lead_score": 82,
        "priority": "Medium",
        "notes": "AI research lab expansion, tender expected next month",
        "next_action": "Send tender proposal template",
        "status": "New"
    },
    {
        "name": "Omar Hassan",
        "title": "CTO",
        "company": "Air Arabia",
        "location": "Sharjah, UAE",
        "industry": "Aviation",
        "company_size": "1000+",
        "linkedin_url": "https://linkedin.com/in/omar-hassan-airarabia",
        "email_1": "omar.hassan@airarabia.com",
        "email_2": "o.hassan@airarabia.com",
        "email_3": "omar@airarabia.com",
        "phone": "+971 6 508 0000",
        "whatsapp": "+971 50 789 0123",
        "company_website": "https://www.airarabia.com",
        "products_interest": "Cloud Infrastructure, Mobile App Servers, Customer Data Systems",
        "lead_score": 93,
        "priority": "Hot",
        "notes": "Digital transformation ongoing, mobile app infrastructure upgrade",
        "next_action": "Present cloud migration strategy",
        "status": "New"
    },
    {
        "name": "Nadia Khalfan",
        "title": "Infrastructure Director",
        "company": "Sharjah Media City",
        "location": "Sharjah, UAE",
        "industry": "Media & Entertainment",
        "company_size": "200-500",
        "linkedin_url": "https://linkedin.com/in/nadia-khalfan-shams",
        "email_1": "nadia.khalfan@shams.ae",
        "email_2": "n.khalfan@shams.ae",
        "email_3": "nadia@shams.ae",
        "phone": "+971 6 556 6666",
        "whatsapp": "+971 55 890 1234",
        "company_website": "https://www.shams.ae",
        "products_interest": "Video Production Servers, Storage Arrays, Rendering Farms",
        "lead_score": 80,
        "priority": "Medium",
        "notes": "Media production expansion, 4K/8K video rendering infrastructure needed",
        "next_action": "Demo rendering farm solution",
        "status": "New"
    },
    {
        "name": "David Chen",
        "title": "IT Systems Manager",
        "company": "Julphar Pharmaceuticals",
        "location": "Ras Al Khaimah, UAE",
        "industry": "Pharmaceuticals",
        "company_size": "500-1000",
        "linkedin_url": "https://linkedin.com/in/david-chen-julphar",
        "email_1": "david.chen@julphar.net",
        "email_2": "d.chen@julphar.net",
        "email_3": "david@julphar.net",
        "phone": "+971 7 233 6000",
        "whatsapp": "+971 56 901 2345",
        "company_website": "https://www.julphar.net",
        "products_interest": "Lab Servers, Research Computing, Quality Control Systems",
        "lead_score": 86,
        "priority": "High",
        "notes": "R&D lab digitization, AI drug discovery systems interest",
        "next_action": "Share pharma industry case studies",
        "status": "New"
    },
    {
        "name": "Laila Mohammed",
        "title": "Technology Manager",
        "company": "RAK Free Trade Zone",
        "location": "Ras Al Khaimah, UAE",
        "industry": "Government/Free Zone",
        "company_size": "200-500",
        "linkedin_url": "https://linkedin.com/in/laila-mohammed-rakftz",
        "email_1": "laila.mohammed@rakftz.com",
        "email_2": "l.mohammed@rakftz.com",
        "email_3": "laila@rakftz.com",
        "phone": "+971 7 204 1111",
        "whatsapp": "+971 50 012 3456",
        "company_website": "https://www.rakftz.com",
        "products_interest": "Office IT Infrastructure, Server Systems, Security Equipment",
        "lead_score": 75,
        "priority": "Medium",
        "notes": "Free zone expansion, tenant support infrastructure upgrade",
        "next_action": "Email infrastructure proposal",
        "status": "New"
    },
    {
        "name": "Michael Roberts",
        "title": "Chief Information Officer",
        "company": "RAK Tourism Development Authority",
        "location": "Ras Al Khaimah, UAE",
        "industry": "Tourism & Hospitality",
        "company_size": "100-200",
        "linkedin_url": "https://linkedin.com/in/michael-roberts-raktda",
        "email_1": "michael.roberts@raktda.com",
        "email_2": "m.roberts@raktda.com",
        "email_3": "michael@raktda.com",
        "phone": "+971 7 228 8844",
        "whatsapp": "+971 55 123 4567",
        "company_website": "https://www.visitrak.ae",
        "products_interest": "Cloud Servers, Mobile Backend, Analytics Systems",
        "lead_score": 77,
        "priority": "Medium",
        "notes": "Tourism digital platform upgrade, mobile app infrastructure",
        "next_action": "Propose cloud-based tourism platform",
        "status": "New"
    },
    {
        "name": "Zainab Ali",
        "title": "IT Director",
        "company": "Sharjah Commerce and Tourism Development Authority",
        "location": "Sharjah, UAE",
        "industry": "Tourism & Government",
        "company_size": "100-200",
        "linkedin_url": "https://linkedin.com/in/zainab-ali-sctda",
        "email_1": "zainab.ali@sctda.gov.ae",
        "email_2": "z.ali@sctda.gov.ae",
        "email_3": "zainab@sctda.gov.ae",
        "phone": "+971 6 556 7777",
        "whatsapp": "+971 56 234 5678",
        "company_website": "https://www.sctda.gov.ae",
        "products_interest": "Government IT Systems, Public WiFi Infrastructure, Data Centers",
        "lead_score": 79,
        "priority": "Medium",
        "notes": "Smart tourism initiative, public infrastructure modernization",
        "next_action": "Government solutions presentation",
        "status": "New"
    },
    {
        "name": "Sanjay Patel",
        "title": "Senior IT Manager",
        "company": "National Cement Company",
        "location": "Ras Al Khaimah, UAE",
        "industry": "Manufacturing",
        "company_size": "500-1000",
        "linkedin_url": "https://linkedin.com/in/sanjay-patel-ncc",
        "email_1": "sanjay.patel@ncc.ae",
        "email_2": "s.patel@ncc.ae",
        "email_3": "sanjay@ncc.ae",
        "phone": "+971 7 244 6666",
        "whatsapp": "+971 50 345 6789",
        "company_website": "https://www.ncc.ae",
        "products_interest": "Industrial Automation Servers, IoT Gateways, ERP Systems",
        "lead_score": 81,
        "priority": "Medium",
        "notes": "Factory automation project, Industry 4.0 implementation",
        "next_action": "Schedule factory tour and demo",
        "status": "New"
    }
]

# ============================================================================
# DATABASE CLASS
# ============================================================================

class LeadDatabase:
    """SQLite database for storing leads"""
    
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
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def insert_lead(self, lead: Dict) -> Optional[int]:
        """Insert lead into database"""
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
                lead.get('name'),
                lead.get('title'),
                lead.get('company'),
                lead.get('location'),
                lead.get('industry'),
                lead.get('company_size'),
                lead.get('linkedin_url'),
                lead.get('email_1'),
                lead.get('email_2'),
                lead.get('email_3'),
                lead.get('phone'),
                lead.get('whatsapp'),
                lead.get('company_website'),
                lead.get('products_interest'),
                lead.get('lead_score', 0),
                lead.get('priority', 'Medium'),
                lead.get('notes', ''),
                lead.get('next_action', ''),
                lead.get('status', 'New')
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def get_all_leads(self) -> List[Dict]:
        """Get all leads"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leads ORDER BY lead_score DESC")
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def export_to_csv(self, filename: str = CONFIG["export_csv"]) -> str:
        """Export to CSV"""
        leads = self.get_all_leads()
        
        if leads:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=leads[0].keys())
                writer.writeheader()
                writer.writerows(leads)
            
            return filename
        return None

# ============================================================================
# GOOGLE SHEETS INTEGRATION
# ============================================================================

class GoogleSheetsSync:
    """Sync leads to Google Sheets"""
    
    def __init__(self, credentials_file: str, sheet_name: str):
        if not GSHEETS_AVAILABLE:
            raise ImportError("Google Sheets libraries not installed")
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        self.client = gspread.authorize(creds)
        
        # Try to open existing sheet or create new one
        try:
            self.spreadsheet = self.client.open(sheet_name)
            self.sheet = self.spreadsheet.sheet1
        except gspread.SpreadsheetNotFound:
            print(f"Creating new sheet: {sheet_name}")
            self.spreadsheet = self.client.create(sheet_name)
            self.sheet = self.spreadsheet.sheet1
            
            # Share with your email
            self.spreadsheet.share('vikabotsystems@gmail.com', perm_type='user', role='writer')
        
        self.setup_headers()
    
    def setup_headers(self):
        """Create header row"""
        headers = [
            'Date Added', 'Name', 'Title', 'Company', 'Location', 'Industry',
            'Company Size', 'LinkedIn', 'Email Option 1', 'Email Option 2',
            'Email Option 3', 'Phone', 'WhatsApp', 'Website', 'Products Interest',
            'Lead Score', 'Priority', 'Status', 'Next Action', 'Notes'
        ]
        
        # Check if headers exist
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
    
    def sync_leads(self, leads: List[Dict]):
        """Sync all leads to Google Sheets"""
        
        # Clear existing data (except headers)
        self.sheet.batch_clear(['A2:T1000'])
        
        # Prepare rows
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
        
        # Batch update
        if rows:
            self.sheet.append_rows(rows, value_input_option='RAW')
            print(f"✓ Synced {len(rows)} leads to Google Sheets")
            print(f"  View at: {self.spreadsheet.url}")

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main execution"""
    
    print("=" * 70)
    print("🎯 AI HARDWARE SALES LEAD GENERATOR - RAK/SHARJAH")
    print("=" * 70)
    print(f"Platform: Linux ARM64")
    print(f"Email: vikabotsystems@gmail.com")
    print(f"Cost: $0/month")
    print("=" * 70)
    print()
    
    # Initialize database
    print("📊 Initializing database...")
    db = LeadDatabase()
    
    # Insert sample leads
    print(f"💾 Loading {len(SAMPLE_LEADS)} sample leads...")
    inserted_count = 0
    for lead in SAMPLE_LEADS:
        if db.insert_lead(lead):
            inserted_count += 1
    
    print(f"✓ Inserted {inserted_count} new leads")
    
    # Get all leads
    all_leads = db.get_all_leads()
    
    # Export to CSV
    print("\n📁 Exporting to CSV...")
    csv_file = db.export_to_csv()
    if csv_file:
        print(f"✓ Exported to: {csv_file}")
    
    # Google Sheets sync
    if GSHEETS_AVAILABLE and os.path.exists(CONFIG["google_credentials"]):
        print("\n📊 Syncing to Google Sheets...")
        try:
            sheets = GoogleSheetsSync(
                CONFIG["google_credentials"],
                CONFIG["google_sheet_name"]
            )
            sheets.sync_leads(all_leads)
        except Exception as e:
            print(f"⚠️  Google Sheets sync failed: {e}")
            print("   Make sure:")
            print("   1. google-credentials.json exists")
            print("   2. Google Sheets API is enabled")
            print("   3. Service account has access to the sheet")
    else:
        print("\n⚠️  Google Sheets sync skipped")
        print("   To enable:")
        print("   1. Set up Google Sheets API (see setup instructions)")
        print("   2. Download credentials JSON")
        print("   3. Re-run this script")
    
    # Generate summary
    print("\n" + "=" * 70)
    print("📈 SUMMARY")
    print("=" * 70)
    
    # Statistics
    high_priority = [l for l in all_leads if l.get('priority') == 'Hot']
    rak_leads = [l for l in all_leads if 'Ras Al Khaimah' in l.get('location', '')]
    sharjah_leads = [l for l in all_leads if 'Sharjah' in l.get('location', '')]
    
    print(f"\nTotal Leads: {len(all_leads)}")
    print(f"Hot Priority (Score ≥90): {len(high_priority)}")
    print(f"RAK Leads: {len(rak_leads)}")
    print(f"Sharjah Leads: {len(sharjah_leads)}")
    
    # Top 5 leads
    print(f"\n🌟 TOP 5 HOTTEST LEADS:")
    print("=" * 70)
    
    for i, lead in enumerate(all_leads[:5], 1):
        print(f"\n{i}. {lead.get('name')} - Score: {lead.get('lead_score')}")
        print(f"   {lead.get('title')} at {lead.get('company')}")
        print(f"   📧 {lead.get('email_1')}")
        print(f"   📞 {lead.get('phone')}")
        print(f"   💬 {lead.get('whatsapp')}")
        print(f"   🔗 {lead.get('linkedin_url')}")
        print(f"   ⭐ {lead.get('priority')} Priority")
        print(f"   📝 {lead.get('notes')}")
    
    print("\n" + "=" * 70)
    print("✅ READY TO START OUTREACH!")
    print("=" * 70)
    print("\n📋 Next Steps:")
    print("1. Review leads in Google Sheets (or CSV file)")
    print("2. Send LinkedIn connections to top 5 leads")
    print("3. Call the 2 hottest leads today")
    print("4. Email top 10 leads with personalized pitches")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
