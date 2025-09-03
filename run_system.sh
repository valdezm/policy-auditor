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
echo "📦 Installing Python dependencies..."
pip install -q fastapi uvicorn pdfplumber PyPDF2 pymupdf sqlalchemy psycopg2-binary 2>/dev/null

# Step 2: Run batch ingestion
echo ""
echo "📥 Ingesting all policies and RT APLs into database..."
echo "   This may take a few minutes on first run..."
cd backend
python ingest_all.py

# Step 3: Start the API server
echo ""
echo "🌐 Starting API server on port 8000..."
if check_port 8000; then
    echo "   Port 8000 is already in use. Skipping API startup."
else
    python api.py &
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