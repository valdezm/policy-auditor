#!/bin/bash

echo "🚀 Policy Auditor - Corpus Coverage System"
echo "=========================================="
echo ""

# Activate virtual environment
source venv/bin/activate

# Step 1: Run batch ingestion
echo "📥 Ingesting all policies and RT APLs into database..."
echo "   This may take a few minutes on first run..."
cd backend
python ingest_all.py

# Step 2: Start the API server
echo ""
echo "🌐 Starting API server on port 8000..."
python api.py &
API_PID=$!
echo "   API running with PID: $API_PID"

# Step 3: Instructions
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
echo "   - http://localhost:8000/"
echo "   - http://localhost:8000/api/coverage/summary"
echo "   - http://localhost:8000/api/policies"
echo "   - http://localhost:8000/api/requirements"
echo ""
echo "Press Ctrl+C to stop the API server..."

# Keep running
wait $API_PID