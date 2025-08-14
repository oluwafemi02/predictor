#!/bin/bash

# Frontend Deployment Fix Script
# This script helps fix the frontend deployment issue on Render

echo "=== Football Prediction Frontend Deployment Fix ==="
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo -e "${RED}Error: render.yaml not found. Please run this script from the project root.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Updating frontend environment configuration...${NC}"

# Navigate to frontend directory
cd football-prediction-app/frontend

# Create production env file
cat > .env.production << EOF
# Production environment variables
REACT_APP_API_URL=https://football-prediction-backend-2cvi.onrender.com
REACT_APP_SPORTMONKS_ENABLED=true
EOF

echo -e "${GREEN}✓ Created .env.production file${NC}"

# Check if build directory exists and is recent
if [ -d "build" ]; then
    echo -e "${YELLOW}Step 2: Build directory exists. Checking if rebuild is needed...${NC}"
    
    # Check if main.js contains the correct backend URL
    if grep -q "football-prediction-backend-2cvi.onrender.com" build/static/js/main.*.js 2>/dev/null; then
        echo -e "${GREEN}✓ Build already contains correct backend URL${NC}"
    else
        echo -e "${YELLOW}Rebuilding frontend with correct environment variables...${NC}"
        REACT_APP_API_URL=https://football-prediction-backend-2cvi.onrender.com npm run build
        echo -e "${GREEN}✓ Frontend rebuilt successfully${NC}"
    fi
else
    echo -e "${YELLOW}Step 2: Building frontend...${NC}"
    REACT_APP_API_URL=https://football-prediction-backend-2cvi.onrender.com npm run build
    echo -e "${GREEN}✓ Frontend built successfully${NC}"
fi

# Return to project root
cd ../..

echo
echo -e "${YELLOW}Step 3: Preparing for deployment...${NC}"

# Check git status
if ! git diff --quiet; then
    echo -e "${YELLOW}Uncommitted changes detected. Committing...${NC}"
    git add .
    git commit -m "Fix frontend deployment: Update API URL to production backend"
    echo -e "${GREEN}✓ Changes committed${NC}"
else
    echo -e "${GREEN}✓ No uncommitted changes${NC}"
fi

echo
echo -e "${GREEN}=== Frontend Fix Complete ===${NC}"
echo
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Push to your repository: git push origin main"
echo "2. Render will automatically detect the push and redeploy"
echo "3. Update environment variables in Render dashboard:"
echo "   - REACT_APP_API_URL = https://football-prediction-backend-2cvi.onrender.com"
echo "   - REACT_APP_SPORTMONKS_ENABLED = true"
echo
echo -e "${YELLOW}Additional Tasks:${NC}"
echo "1. Populate database with upcoming matches"
echo "2. Configure SportMonks API keys in backend"
echo "3. Enable scheduler service for automatic updates"
echo
echo "For detailed instructions, see FRONTEND_DEPLOYMENT_FIX.md"