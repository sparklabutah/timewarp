#!/bin/bash
# Start Wikinews application

echo "Starting Wikinews UI..."
echo "Make sure you have Flask installed: pip install -r requirements.txt"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the Flask app
python news_app.py

