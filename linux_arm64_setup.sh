#!/bin/bash
# Complete Setup Script for Linux ARM64
# AI Hardware Sales Lead Generator with Google Sheets Integration

echo "======================================================================"
echo "🚀 AI Hardware Sales Lead Generator - Linux ARM64 Setup"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}1. Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python found: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
else
    echo -e "${RED}✗ Python 3 not found. Please install it first.${NC}"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install python3 python3-pip"
    exit 1
fi

# Check pip
echo -e "${YELLOW}2. Checking pip...${NC}"
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓ pip3 found${NC}"
else
    echo -e "${RED}✗ pip not found. Installing...${NC}"
    sudo apt-get install -y python3-pip
fi

# Install required packages
echo -e "${YELLOW}3. Installing Python packages...${NC}"
echo "   This may take a few minutes..."

$PIP_CMD install --upgrade pip
$PIP_CMD install beautifulsoup4 requests gspread google-auth google-auth-oauthlib google-auth-httplib2

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All packages installed successfully${NC}"
else
    echo -e "${RED}✗ Package installation failed${NC}"
    exit 1
fi

# Create project directory
echo -e "${YELLOW}4. Creating project directory...${NC}"
mkdir -p ~/ai-hardware-sales
cd ~/ai-hardware-sales

echo -e "${GREEN}✓ Project directory created: ~/ai-hardware-sales${NC}"

# Create main scraper file
echo -e "${YELLOW}5. Creating scraper script...${NC}"
cat > lead_scraper.py << 'PYTHON_SCRIPT_END'
# Copy the complete Python script here - see next artifact
PYTHON_SCRIPT_END

echo -e "${GREEN}✓ Scraper script created${NC}"

# Setup instructions
echo ""
echo "======================================================================"
echo "📋 GOOGLE SHEETS API SETUP INSTRUCTIONS"
echo "======================================================================"
echo ""
echo "Follow these steps to enable Google Sheets API:"
echo ""
echo "1. Go to: https://console.cloud.google.com"
echo "   - Sign in with: vikabotsystems@gmail.com"
echo ""
echo "2. Create New Project:"
echo "   - Click 'Select a project' → 'New Project'"
echo "   - Name: 'AI-Hardware-Sales'"
echo "   - Click 'Create'"
echo ""
echo "3. Enable Google Sheets API:"
echo "   - In the search bar, type 'Google Sheets API'"
echo "   - Click on it → Click 'Enable'"
echo ""
echo "4. Create Service Account:"
echo "   - Go to 'Credentials' (left menu)"
echo "   - Click 'Create Credentials' → 'Service Account'"
echo "   - Name: 'sales-lead-scraper'"
echo "   - Click 'Create and Continue'"
echo "   - Skip optional steps → Click 'Done'"
echo ""
echo "5. Create Key:"
echo "   - Click on the service account you just created"
echo "   - Go to 'Keys' tab"
echo "   - Click 'Add Key' → 'Create new key'"
echo "   - Choose 'JSON'"
echo "   - Click 'Create'"
echo "   - File will download automatically"
echo ""
echo "6. Move the downloaded file:"
echo "   mv ~/Downloads/ai-hardware-sales-*.json ~/ai-hardware-sales/google-credentials.json"
echo ""
echo "7. Create Google Sheet:"
echo "   - Go to: https://sheets.google.com"
echo "   - Create new spreadsheet"
echo "   - Name it: 'AI Hardware Sales Leads - RAK Sharjah'"
echo "   - Share it with the service account email (from the JSON file)"
echo "   - Give 'Editor' permission"
echo "   - Copy the Sheet URL"
echo ""
echo "======================================================================"
echo ""

# Create config file template
cat > config.json << 'EOF'
{
  "google_credentials": "google-credentials.json",
  "google_sheet_url": "PASTE_YOUR_GOOGLE_SHEET_URL_HERE",
  "target_regions": ["Ras Al Khaimah", "Sharjah"],
  "target_titles": [
    "IT Director",
    "CTO",
    "CIO",
    "VP of IT",
    "Technology Director",
    "IT Manager",
    "Infrastructure Manager"
  ]
}
EOF

echo -e "${GREEN}✓ Configuration template created: config.json${NC}"
echo ""

# Create quick start script
cat > run.sh << 'EOF'
#!/bin/bash
cd ~/ai-hardware-sales
python3 lead_scraper.py
EOF

chmod +x run.sh

echo -e "${GREEN}✓ Quick run script created: run.sh${NC}"
echo ""

# Final instructions
echo "======================================================================"
echo "✅ INSTALLATION COMPLETE!"
echo "======================================================================"
echo ""
echo "📁 Project Location: ~/ai-hardware-sales"
echo ""
echo "🔑 NEXT STEPS:"
echo ""
echo "1. Set up Google Sheets API (follow instructions above)"
echo ""
echo "2. Edit config.json and add your Google Sheet URL:"
echo "   nano ~/ai-hardware-sales/config.json"
echo ""
echo "3. Run the scraper:"
echo "   cd ~/ai-hardware-sales"
echo "   ./run.sh"
echo ""
echo "   OR directly:"
echo "   python3 lead_scraper.py"
echo ""
echo "======================================================================"
echo ""
echo "📊 Expected Output:"
echo "   • SQLite database with 15 sample leads"
echo "   • CSV export files"
echo "   • Auto-sync to Google Sheets"
echo "   • Lead scoring and prioritization"
echo ""
echo "======================================================================"
