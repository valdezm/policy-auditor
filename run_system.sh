#!/bin/bash

echo "🚀 Policy Auditor - Corpus Coverage System"
echo "=========================================="
echo ""

# Function to check if port is in use
check_port() {
    lsof -i:$1 > /dev/null 2>&1
    return $?
}

# Step 1: Install dependencies
echo "📦 Checking Python dependencies..."
# Check if pip is installed
if ! python3 -m pip --version &>/dev/null; then
    echo "   Installing pip..."
    sudo apt-get update && sudo apt-get install -y python3-pip
fi

echo "   Installing required packages..."
python3 -m pip install --user fastapi uvicorn pdfplumber PyPDF2 pymupdf sqlalchemy psycopg2-binary 2>/dev/null || {
    echo "   Some packages may not have installed. Continuing anyway..."
}

# Step 2: Run batch ingestion
echo ""
echo "📥 Ingesting all policies and RT APLs into database..."
echo "   This may take a few minutes on first run..."
cd backend
python3 ingest_all.py

# Step 3: Start the API server
echo ""
echo "🌐 Starting API server on port 8000..."
if check_port 8000; then
    echo "   Port 8000 is already in use. Skipping API startup."
else
    python3 api.py &
    API_PID=$!
    echo "   API running with PID: $API_PID"
fi

# Step 4: Instructions for the frontend
echo ""
echo "📊 To view the coverage dashboard:"
echo "   1. Open a new terminal"
echo "   2. cd frontend-next"
echo "   3. npm install (first time only)"
echo "   4. npm run dev"
echo "   5. Open http://localhost:3000/coverage-view"
echo ""
echo "✅ System ready!"
echo ""
echo "API Endpoints:"
echo "   - http://localhost:8000/api/coverage/summary"
echo "   - http://localhost:8000/api/policies"
echo "   - http://localhost:8000/api/requirements"
echo ""

# Keep the script running
if [ ! -z "$API_PID" ]; then
    echo "Press Ctrl+C to stop the API server..."
    wait $API_PID
fi