# AI Text Summarizer

A Flask-based web application that provides intelligent text summarization using state-of-the-art NLP models. The application supports both text input and document uploads (TXT and DOCX formats), generates concise summaries, extracts key entities, and provides detailed analytics about the summarization process.

## Features

- Text and document (TXT, DOCX) summarization
- Named Entity Recognition
- Summary history tracking
- PDF report generation
- Compression ratio calculation
- Responsive web interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Anshika09Singh/ai-summarizer.git
cd ai-summarizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

3. Run the application:
```bash
python app.py
```

## Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Quick Deploy Steps:

1. **Push to GitHub** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Render**:
   - Go to [render.com](https://render.com)
   - Click "New" → "Web Service"  
   - Connect your GitHub repository
   - Use these settings:
     - **Build Command**: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
     - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`

See [DEPLOY.md](DEPLOY.md) for detailed deployment instructions.

The application will be available at `http://localhost:5000`

## Usage

1. Visit the web interface
2. Either paste text or upload a document
3. Adjust summary length if needed
4. Click "Summarize" to generate the summary
5. View extracted entities and analytics
6. Download PDF report if desired

## Technologies Used

- Flask
- Transformers (BART model for summarization)
- SpaCy (for Named Entity Recognition)
- Beautiful Soup 4
- ReportLab (PDF generation)
- python-docx 