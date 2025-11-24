"""
AI Hardware Sales Intelligence Platform for UAE Market
Automated B2B lead generation, enrichment, and CRM for IT hardware sales

Target: IT Procurement Managers, Directors, VPs
Focus: Compute Servers, Desktop/Rack-Tower, AMC, Vending Machines
Output: Google Sheets + LinkedIn Automation + Follow-up Dashboard
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from enum import Enum
import json

# ============================================================================
# 1. DATA MODELS
# ============================================================================

class JobTitle(Enum):
    """Target job titles for IT procurement"""
    IT_DIRECTOR = "IT Director"
    IT_MANAGER = "IT Manager"
    PROCUREMENT_MANAGER = "Procurement Manager"
    TECHNOLOGY_MANAGER = "Technology Manager"
    VP_IT = "VP of IT"
    VP_TECHNOLOGY = "VP of Technology"
    CTO = "Chief Technology Officer"
    CIO = "Chief Information Officer"
    HEAD_IT = "Head of IT"
    INFRASTRUCTURE_MANAGER = "Infrastructure Manager"
    DATA_CENTER_MANAGER = "Data Center Manager"

class ProductInterest(Enum):
    """Hardware product categories"""
    DESKTOP_COMPUTE = "Desktop Computers"
    RACK_SERVERS = "Rack Servers"
    TOWER_SERVERS = "Tower Servers"
    GPU_SERVERS = "GPU Servers (AI/ML)"
    STORAGE_SYSTEMS = "Storage Systems"
    NETWORKING = "Networking Equipment"
    AMC_CONTRACTS = "AMC/Maintenance Contracts"
    VENDING_MACHINES = "IT Vending Machines"

class LeadStatus(Enum):
    """Lead pipeline stages"""
    NEW = "new"
    ENRICHED = "enriched"
    LINKEDIN_PENDING = "linkedin_pending"
    LINKEDIN_CONNECTED = "linkedin_connected"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    QUALIFIED = "qualified"
    MEETING_SCHEDULED = "meeting_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"

@dataclass
class Lead:
    """Complete lead information"""
    # Basic Info
    id: str
    company_name: str
    contact_name: str
    job_title: str
    
    # Contact Details
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    # Company Details
    company_website: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    location: str = "UAE"
    city: Optional[str] = None
    
    # Intelligence
    product_interests: List[ProductInterest] = None
    tech_stack: List[str] = None
    current_vendors: List[str] = None
    budget_estimate: Optional[str] = None
    
    # Engagement Tracking
    status: LeadStatus = LeadStatus.NEW
    lead_score: float = 0.0
    first_contact_date: Optional[datetime] = None
    last_contact_date: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None
    
    # LinkedIn Automation
    linkedin_connection_sent: bool = False
    linkedin_connection_accepted: bool = False
    linkedin_message_sent: bool = False
    linkedin_response_received: bool = False
    
    # Notes & Activity
    notes: str = ""
    activity_log: List[Dict] = None
    
    # Metadata
    source: str = ""
    created_at: datetime = None
    updated_at: datetime = None

# ============================================================================
# 2. LINKEDIN SALES NAVIGATOR SCRAPER
# ============================================================================

class LinkedInSalesNavigatorScraper:
    """
    Scrape LinkedIn Sales Navigator for IT decision makers
    
    Requirements:
    - LinkedIn Sales Navigator subscription
    - Valid session cookies
    - Rate limiting to avoid blocks
    
    Alternative: Use LinkedIn API if available
    """
    
    def __init__(self, session_cookie: str):
        self.session_cookie = session_cookie
        self.base_url = "https://www.linkedin.com/sales"
        self.daily_search_limit = 100  # Sales Nav limit
        
    def search_decision_makers(self, 
                               titles: List[str],
                               location: str = "United Arab Emirates",
                               company_size: str = "51-200",
                               industries: List[str] = None) -> List[Dict]:
        """
        Search for IT decision makers using Sales Navigator
        
        Filters:
        - Job Titles: IT Director, CTO, VP IT, etc.
        - Location: UAE (Dubai, Abu Dhabi, RAK)
        - Company Size: 51-200, 201-500, 501-1000+
        - Industries: IT Services, Tech, Manufacturing, Retail, etc.
        - Keywords: "IT procurement", "hardware", "infrastructure"
        """
        
        search_params = {
            'titles': titles,
            'location': location,
            'companySize': company_size,
            'keywords': 'IT hardware OR server OR infrastructure OR procurement'
        }
        
        # Implementation would use LinkedIn Sales Navigator API
        # or browser automation (Selenium) with session cookies
        
        leads = []
        
        # Pseudo-code for search
        """
        1. Build search URL with filters
        2. Execute search
        3. Extract profile information:
           - Name, Title, Company
           - LinkedIn profile URL
           - Company details
           - Mutual connections
           - Recent activity
        4. Return structured data
        """
        
        return leads
    
    def enrich_profile(self, linkedin_url: str) -> Dict:
        """
        Get detailed profile information
        
        Extracts:
        - Full name and current position
        - Company details (size, industry, website)
        - Email (if available)
        - Phone (if available)
        - Skills and endorsements
        - Recent posts/activity
        - Mutual connections
        """
        pass
    
    def get_company_employees(self, company_name: str, 
                              titles: List[str]) -> List[Dict]:
        """
        Find all decision makers in a specific company
        """
        pass

# ============================================================================
# 3. B2B CONTACT ENRICHMENT
# ============================================================================

class ContactEnrichment:
    """
    Enrich leads with contact information from multiple sources
    
    Services to integrate:
    - Hunter.io (email finding)
    - RocketReach (phone + email)
    - Lusha (B2B contacts)
    - Clearbit (company data)
    - ZoomInfo (comprehensive B2B data)
    """
    
    def __init__(self, api_keys: Dict[str, str]):
        self.hunter_key = api_keys.get('hunter_io')
        self.rocketreach_key = api_keys.get('rocketreach')
        self.clearbit_key = api_keys.get('clearbit')
    
    def find_email(self, first_name: str, last_name: str, 
                   company_domain: str) -> Optional[str]:
        """
        Find email using Hunter.io
        
        API: https://hunter.io/api/v2/email-finder
        """
        # Hunter.io API implementation
        pass
    
    def find_phone(self, full_name: str, company_name: str, 
                   location: str = "UAE") -> Optional[str]:
        """
        Find phone number using RocketReach or Lusha
        """
        pass
    
    def find_whatsapp(self, phone: str) -> Optional[str]:
        """
        Check if phone number has WhatsApp
        Uses WhatsApp Business API or validation services
        """
        # Format: +971XXXXXXXXX
        if phone and phone.startswith('+971'):
            # Mobile numbers in UAE: +971 5X XXX XXXX
            if '5' in phone[4:6]:
                return phone  # Likely has WhatsApp
        return None
    
    def enrich_company_data(self, company_domain: str) -> Dict:
        """
        Get company information from Clearbit
        
        Returns:
        - Employee count
        - Revenue estimate
        - Industry
        - Tech stack
        - Social profiles
        """
        pass
    
    def get_tech_stack(self, company_domain: str) -> List[str]:
        """
        Identify company's technology stack
        
        Services:
        - BuiltWith
        - Wappalyzer
        - Clearbit
        
        Returns: ['AWS', 'Microsoft Azure', 'VMware', 'Dell', 'HPE']
        """
        pass

# ============================================================================
# 4. GOOGLE SHEETS INTEGRATION
# ============================================================================

class GoogleSheetsManager:
    """
    Sync leads to Google Sheets in real-time
    
    Requirements:
    - Google Sheets API credentials
    - Service account JSON key
    - Sheet ID
    """
    
    def __init__(self, credentials_path: str, sheet_id: str):
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.sheet_id = sheet_id
    
    def create_leads_sheet(self):
        """
        Create structured sheet with tabs:
        - All Leads
        - New Leads (Today)
        - In Progress
        - Qualified
        - Won/Lost
        """
        
        headers = [
            'Lead ID', 'Date Added', 'Company Name', 'Contact Name', 
            'Job Title', 'Email', 'Phone', 'WhatsApp', 'LinkedIn',
            'City', 'Company Size', 'Industry', 'Product Interest',
            'Lead Score', 'Status', 'Last Contact', 'Next Follow-up',
            'LinkedIn Connected', 'Notes', 'Assigned To'
        ]
        
        # Create sheet structure
        pass
    
    def append_lead(self, lead: Lead):
        """
        Add new lead to Google Sheets
        Updates daily automatically
        """
        
        row = [
            lead.id,
            lead.created_at.strftime('%Y-%m-%d'),
            lead.company_name,
            lead.contact_name,
            lead.job_title,
            lead.email or '',
            lead.phone or '',
            lead.whatsapp or '',
            lead.linkedin_url or '',
            lead.city or '',
            lead.company_size or '',
            lead.industry or '',
            ', '.join([p.value for p in lead.product_interests]) if lead.product_interests else '',
            lead.lead_score,
            lead.status.value,
            lead.last_contact_date.strftime('%Y-%m-%d') if lead.last_contact_date else '',
            lead.next_follow_up.strftime('%Y-%m-%d') if lead.next_follow_up else '',
            'Yes' if lead.linkedin_connection_accepted else 'No',
            lead.notes,
            ''  # Assigned sales rep
        ]
        
        # Append to sheet
        range_name = 'All Leads!A:T'
        body = {'values': [row]}
        
        self.service.spreadsheets().values().append(
            spreadsheetId=self.sheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
    
    def update_lead(self, lead_id: str, updates: Dict):
        """
        Update existing lead in sheet
        """
        pass
    
    def get_todays_leads(self) -> List[Dict]:
        """
        Fetch all leads added today
        """
        pass
    
    def bulk_update(self, leads: List[Lead]):
        """
        Batch update multiple leads
        """
        pass

# ============================================================================
# 5. LINKEDIN AUTOMATION
# ============================================================================

class LinkedInAutomation:
    """
    Automate LinkedIn connection requests and messaging
    
    IMPORTANT: Use carefully to avoid LinkedIn restrictions
    - Max 100 connection requests/week
    - Max 250 messages/day (for premium)
    - Personalize each message
    - Add delays between actions
    
    Recommended: Use LinkedIn Sales Navigator + LinkedIn Helper tools
    Alternative: Phantombuster, Dux-Soup, Expandi.io
    """
    
    def __init__(self, session_cookie: str):
        self.session_cookie = session_cookie
        self.daily_connection_limit = 15  # Stay safe
        self.connections_sent_today = 0
        
    def send_connection_request(self, 
                                linkedin_url: str,
                                contact_name: str,
                                company_name: str,
                                job_title: str) -> bool:
        """
        Send personalized connection request
        
        Template: Customize based on context
        """
        
        if self.connections_sent_today >= self.daily_connection_limit:
            print("⚠️  Daily connection limit reached")
            return False
        
        # Generate personalized message
        message = self.generate_connection_message(
            contact_name, company_name, job_title
        )
        
        # Send connection request via API or automation
        # Implementation would use LinkedIn automation tool
        
        self.connections_sent_today += 1
        return True
    
    def generate_connection_message(self, 
                                    contact_name: str,
                                    company_name: str,
                                    job_title: str) -> str:
        """
        Generate personalized connection request message
        
        Template variables:
        - {name}: Contact's first name
        - {company}: Company name
        - {title}: Job title
        - {mutual}: Mutual connections count
        """
        
        templates = [
            """Hi {name},

I noticed your role at {company} and wanted to connect. We specialize in AI-powered hardware solutions for UAE enterprises.

I'd love to explore how we can support {company}'s infrastructure needs.

Best regards,
[Your Name]""",

            """Hello {name},

As {title} at {company}, I thought you might be interested in our latest GPU servers and AI compute solutions tailored for the UAE market.

Would be great to connect!

[Your Name]""",

            """Hi {name},

I help companies like {company} optimize their IT infrastructure with cost-effective server solutions and AMC contracts.

Let's connect to explore potential synergies.

[Your Name]"""
        ]
        
        # Select template and personalize
        import random
        template = random.choice(templates)
        
        first_name = contact_name.split()[0]
        
        return template.format(
            name=first_name,
            company=company_name,
            title=job_title
        )
    
    def send_follow_up_message(self, linkedin_url: str, 
                               lead: Lead) -> bool:
        """
        Send message after connection is accepted
        """
        
        message = f"""Hi {lead.contact_name.split()[0]},

Thanks for connecting! I wanted to share how we've helped companies similar to {lead.company_name} with:

• AI/ML GPU Servers (NVIDIA, AMD)
• Enterprise Rack/Tower Servers
• Comprehensive AMC Contracts
• IT Infrastructure Consulting

Would you be open to a brief call next week to discuss {lead.company_name}'s current IT needs?

Best regards,
[Your Name]
[Your Company]
[Your Phone]"""
        
        # Send via LinkedIn API or automation
        pass
    
    def check_connection_status(self, linkedin_url: str) -> str:
        """
        Check if connection request was accepted
        """
        pass

# ============================================================================
# 6. LEAD SCORING ENGINE
# ============================================================================

class LeadScoringEngine:
    """
    Score leads based on multiple factors
    0-100 scale
    """
    
    @staticmethod
    def calculate_score(lead: Lead) -> float:
        """
        Calculate lead score based on:
        - Job title seniority
        - Company size
        - Contact completeness
        - Tech stack match
        - Engagement level
        """
        
        score = 0.0
        
        # Job Title Score (0-30 points)
        title_scores = {
            'CTO': 30, 'CIO': 30, 'VP': 25,
            'Director': 20, 'Manager': 15, 'Head': 20
        }
        
        for keyword, points in title_scores.items():
            if keyword.lower() in lead.job_title.lower():
                score += points
                break
        
        # Company Size Score (0-20 points)
        if lead.company_size:
            size_scores = {
                '1000+': 20, '501-1000': 18, '201-500': 15,
                '51-200': 12, '11-50': 8
            }
            score += size_scores.get(lead.company_size, 5)
        
        # Contact Completeness (0-25 points)
        if lead.email: score += 10
        if lead.phone: score += 8
        if lead.linkedin_url: score += 7
        
        # Tech Stack Match (0-15 points)
        if lead.tech_stack:
            relevant_tech = ['AWS', 'Azure', 'Dell', 'HPE', 'Cisco', 'VMware']
            matches = len(set(lead.tech_stack) & set(relevant_tech))
            score += min(matches * 5, 15)
        
        # Engagement Score (0-10 points)
        if lead.linkedin_connection_accepted: score += 5
        if lead.linkedin_response_received: score += 5
        
        return min(score, 100.0)

# ============================================================================
# 7. COMMUNICATION TRACKING DASHBOARD
# ============================================================================

class CommunicationDashboard:
    """
    Track all interactions with leads
    
    Features:
    - Activity timeline
    - Next follow-up schedule
    - Response tracking
    - Meeting scheduler
    - Proposal tracker
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def log_activity(self, lead_id: str, 
                     activity_type: str, 
                     details: str,
                     next_action: Optional[datetime] = None):
        """
        Log communication activity
        
        Activity Types:
        - linkedin_connection_sent
        - linkedin_message_sent
        - email_sent
        - call_made
        - meeting_held
        - proposal_sent
        - follow_up_required
        """
        
        activity = {
            'lead_id': lead_id,
            'timestamp': datetime.now(),
            'type': activity_type,
            'details': details,
            'next_action': next_action,
            'completed_by': 'System'  # or sales rep name
        }
        
        # Store in database
        pass
    
    def get_follow_up_schedule(self, days_ahead: int = 7) -> List[Dict]:
        """
        Get all leads requiring follow-up in next N days
        """
        
        query = """
        SELECT * FROM leads 
        WHERE next_follow_up BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL ? DAY)
        ORDER BY next_follow_up ASC
        """
        
        # Execute and return
        pass
    
    def get_lead_timeline(self, lead_id: str) -> List[Dict]:
        """
        Get complete activity history for a lead
        """
        pass
    
    def update_lead_status(self, lead_id: str, 
                          new_status: LeadStatus,
                          notes: str = ""):
        """
        Update lead pipeline stage
        """
        pass

# ============================================================================
# 8. MAIN ORCHESTRATOR
# ============================================================================

class SalesIntelligencePlatform:
    """
    Main orchestrator for the entire sales intelligence system
    """
    
    def __init__(self, config: Dict):
        self.linkedin_scraper = LinkedInSalesNavigatorScraper(
            config['linkedin_session']
        )
        self.enrichment = ContactEnrichment(config['api_keys'])
        self.sheets = GoogleSheetsManager(
            config['google_credentials'],
            config['sheet_id']
        )
        self.linkedin_automation = LinkedInAutomation(
            config['linkedin_session']
        )
        self.scoring = LeadScoringEngine()
        self.dashboard = CommunicationDashboard(config['db_connection'])
    
    def daily_lead_generation(self):
        """
        Daily automated workflow
        
        Steps:
        1. Search LinkedIn Sales Navigator for new leads
        2. Enrich with contact information
        3. Calculate lead scores
        4. Push to Google Sheets
        5. Initiate LinkedIn connections (top leads only)
        6. Update dashboard
        """
        
        print("🚀 Starting daily lead generation...")
        
        # Step 1: Search for decision makers
        target_titles = [
            "IT Director", "IT Manager", "CTO", "CIO",
            "VP IT", "VP Technology", "Infrastructure Manager"
        ]
        
        raw_leads = self.linkedin_scraper.search_decision_makers(
            titles=target_titles,
            location="United Arab Emirates",
            company_size="51-200"
        )
        
        print(f"✓ Found {len(raw_leads)} potential leads")
        
        # Step 2: Enrich each lead
        enriched_leads = []
        for raw_lead in raw_leads:
            lead = self.enrich_lead(raw_lead)
            enriched_leads.append(lead)
        
        print(f"✓ Enriched {len(enriched_leads)} leads")
        
        # Step 3: Score and filter
        high_quality_leads = [
            lead for lead in enriched_leads 
            if lead.lead_score >= 50
        ]
        
        print(f"✓ {len(high_quality_leads)} high-quality leads (score ≥50)")
        
        # Step 4: Push to Google Sheets
        for lead in enriched_leads:
            self.sheets.append_lead(lead)
        
        print(f"✓ Pushed to Google Sheets")
        
        # Step 5: Initiate LinkedIn connections (top 15 only)
        top_leads = sorted(
            high_quality_leads, 
            key=lambda x: x.lead_score, 
            reverse=True
        )[:15]
        
        for lead in top_leads:
            if not lead.linkedin_connection_sent:
                success = self.linkedin_automation.send_connection_request(
                    lead.linkedin_url,
                    lead.contact_name,
                    lead.company_name,
                    lead.job_title
                )
                
                if success:
                    lead.linkedin_connection_sent = True
                    lead.status = LeadStatus.LINKEDIN_PENDING
                    
                    self.dashboard.log_activity(
                        lead.id,
                        'linkedin_connection_sent',
                        f"Sent connection request via automation",
                        next_action=datetime.now() + timedelta(days=3)
                    )
        
        print(f"✓ Sent {len(top_leads)} LinkedIn connection requests")
        
        # Step 6: Generate daily report
        self.generate_daily_report(enriched_leads, high_quality_leads)
    
    def enrich_lead(self, raw_lead: Dict) -> Lead:
        """
        Enrich a single lead with all available information
        """
        
        lead = Lead(
            id=raw_lead['id'],
            company_name=raw_lead['company'],
            contact_name=raw_lead['name'],
            job_title=raw_lead['title'],
            linkedin_url=raw_lead['linkedin_url']
        )
        
        # Find email
        if 'company_domain' in raw_lead:
            first_name = raw_lead['name'].split()[0]
            last_name = raw_lead['name'].split()[-1]
            lead.email = self.enrichment.find_email(
                first_name, last_name, raw_lead['company_domain']
            )
        
        # Find phone
        lead.phone = self.enrichment.find_phone(
            raw_lead['name'], 
            raw_lead['company'],
            'UAE'
        )
        
        # Check WhatsApp
        if lead.phone:
            lead.whatsapp = self.enrichment.find_whatsapp(lead.phone)
        
        # Get company data
        if 'company_domain' in raw_lead:
            company_data = self.enrichment.enrich_company_data(
                raw_lead['company_domain']
            )
            lead.company_size = company_data.get('size')
            lead.industry = company_data.get('industry')
        
        # Get tech stack
        if 'company_domain' in raw_lead:
            lead.tech_stack = self.enrichment.get_tech_stack(
                raw_lead['company_domain']
            )
        
        # Calculate lead score
        lead.lead_score = self.scoring.calculate_score(lead)
        
        # Set metadata
        lead.source = "LinkedIn Sales Navigator"
        lead.created_at = datetime.now()
        lead.updated_at = datetime.now()
        
        return lead
    
    def generate_daily_report(self, all_leads: List[Lead], 
                             high_quality: List[Lead]):
        """
        Generate and email daily summary report
        """
        
        report = f"""
Daily Sales Intelligence Report - {datetime.now().strftime('%Y-%m-%d')}
{'=' * 70}

NEW LEADS: {len(all_leads)}
HIGH-QUALITY LEADS (Score ≥50): {len(high_quality)}

TOP 10 LEADS:
"""
        
        for i, lead in enumerate(sorted(high_quality, key=lambda x: x.lead_score, reverse=True)[:10], 1):
            report += f"""
{i}. {lead.contact_name} - {lead.job_title}
   Company: {lead.company_name}
   Score: {lead.lead_score:.1f}
   Email: {lead.email or 'N/A'}
   Phone: {lead.phone or 'N/A'}
   LinkedIn: {lead.linkedin_url}
"""
        
        # Send via email
        print(report)

# ============================================================================
# 9. CONFIGURATION
# ============================================================================

def get_config() -> Dict:
    """Load configuration"""
    return {
        'linkedin_session': 'your_linkedin_session_cookie',
        'google_credentials': 'path/to/google-credentials.json',
        'sheet_id': 'your_google_sheet_id',
        'db_connection': 'sqlite:///sales_intelligence.db',
        
        'api_keys': {
            'hunter_io': 'your_hunter_key',
            'rocketreach': 'your_rocketreach_key',
            'clearbit': 'your_clearbit_key'
        }
    }

# ============================================================================
# USAGE
# ============================================================================

if __name__ == "__main__":
    config = get_config()
    platform = SalesIntelligencePlatform(config)
    
    # Run daily lead generation
    platform.daily_lead_generation()
