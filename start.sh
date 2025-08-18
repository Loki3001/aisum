#!/bin/bash
# Render startup script

echo "Starting AI Summarizer deployment..."

# Download spaCy model if not exists
python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null || python -m spacy download en_core_web_sm

echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app
