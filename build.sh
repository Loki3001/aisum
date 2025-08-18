#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Create necessary directories
mkdir -p static/uploads
mkdir -p logs

echo "Build completed successfully!"
