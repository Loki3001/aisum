from flask import Flask, render_template, request, jsonify, send_file
from bs4 import BeautifulSoup
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not available. Entity extraction will be disabled.")
import re
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not available. DOCX file reading will be disabled.")
from datetime import datetime
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load models - using simple extractive summarization for now
# summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
TRANSFORMER_AVAILABLE = False
try:
    from transformers import pipeline
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    TRANSFORMER_AVAILABLE = True
    logger.info("Transformers loaded successfully")
except Exception as e:
    logger.warning(f"Transformers not available ({str(e)}). Using fallback summarization.")
    TRANSFORMER_AVAILABLE = False
if SPACY_AVAILABLE:
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("Warning: spaCy English model not found. Installing...")
        SPACY_AVAILABLE = False

# Store summary history
HISTORY_FILE = 'summary_history.json'

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_to_history(original_text, summary, entities, word_count, timestamp):
    history = load_history()
    entry = {
        'id': len(history) + 1,
        'timestamp': timestamp,
        'original_word_count': word_count,
        'original_text': original_text[:200] + "..." if len(original_text) > 200 else original_text,
        'summary': summary,
        'entities': entities,
        'summary_word_count': len(summary.split())
    }
    history.append(entry)
    
    # Keep only last 50 summaries
    if len(history) > 50:
        history = history[-50:]
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def clean_text(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text()
    return re.sub(r'\s+', ' ', text).strip()

def extract_entities(text):
    if not SPACY_AVAILABLE:
        # Return some basic entities using simple pattern matching as fallback
        import re
        entities = []
        
        # Simple regex patterns for common entities
        # Dates
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
        dates = re.findall(date_pattern, text)
        for date in dates[:5]:
            entities.append((date, "DATE"))
        
        # Numbers/Money
        money_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|million|billion)\b'
        money = re.findall(money_pattern, text, re.IGNORECASE)
        for amount in money[:5]:
            entities.append((amount, "MONEY"))
        
        # Capitalized words (potential names/organizations)
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        names = re.findall(name_pattern, text)
        for name in names[:10]:
            if len(name) > 3:  # Filter out short words
                entities.append((name, "PERSON/ORG"))
        
        return entities[:20]
    
    doc = nlp(text)
    entities = []
    seen = set()
    for ent in doc.ents:
        if ent.text not in seen and len(ent.text.strip()) > 1:
            entities.append((ent.text, ent.label_))
            seen.add(ent.text)
    return entities[:20]  # Limit to 20 entities

def generate_summary(text, max_words=150, min_words=30):
    input_length = len(text.split())
    
    # Improved word limitation logic
    if input_length < 50:
        return "Text too short for meaningful summarization. Please provide at least 50 words."
    
    if TRANSFORMER_AVAILABLE:
        # Handle very long texts by chunking
        if input_length > 1000:
            # Split into chunks and summarize each
            words = text.split()
            chunk_size = 800
            chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
            
            summaries = []
            for chunk in chunks:
                try:
                    chunk_summary = summarizer(chunk, 
                                             max_length=min(100, int(len(chunk.split()) * 0.3)), 
                                             min_length=20, 
                                             do_sample=False)[0]['summary_text']
                    summaries.append(chunk_summary)
                except Exception as e:
                    continue
            
            # Combine and re-summarize if needed
            combined = ' '.join(summaries)
            if len(combined.split()) > max_words:
                return summarizer(combined, 
                                max_length=max_words, 
                                min_length=min_words, 
                                do_sample=False)[0]['summary_text']
            return combined
        
        # Regular summarization for normal-length texts
        try:
            # Dynamic length calculation
            max_len = min(max_words, max(min_words, int(input_length * 0.4)))
            return summarizer(text, 
                             max_length=max_len, 
                             min_length=min_words, 
                             do_sample=False)[0]['summary_text']
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    else:
        # Fallback: Simple extractive summarization
        sentences = text.split('. ')
        if len(sentences) <= 3:
            return text
        
        # Score sentences by their position and common words
        scores = {}
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        for i, sentence in enumerate(sentences):
            score = 0
            sentence_words = sentence.lower().split()
            
            # Position score (earlier sentences get higher score)
            score += (len(sentences) - i) / len(sentences) * 0.3
            
            # Word frequency score
            for word in sentence_words:
                if word in word_freq:
                    score += word_freq[word]
            
            # Length penalty (very short or long sentences get lower score)
            length = len(sentence_words)
            if 10 <= length <= 30:
                score += 0.2
            
            scores[i] = score
        
        # Select top sentences
        target_sentences = max(2, min(5, int(len(sentences) * 0.3)))
        top_sentences = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:target_sentences]
        top_sentences.sort()  # Maintain original order
        
        summary = '. '.join([sentences[i] for i in top_sentences])
        if not summary.endswith('.'):
            summary += '.'
            
        return summary

def read_file(file):
    try:
        if file.filename.endswith(".txt"):
            return file.read().decode("utf-8")
        elif file.filename.endswith(".docx"):
            if not DOCX_AVAILABLE:
                return "Error: DOCX file reading not available. Please install python-docx or convert to TXT format."
            doc = Document(file)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            return "Error: Unsupported file format. Please use .txt or .docx files."
    except Exception as e:
        return f"Error reading file: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Read file content
        content = read_file(file)
        if content.startswith("Error"):
            return jsonify({'success': False, 'error': content})
        
        word_count = len(content.split())
        
        return jsonify({
            'success': True,
            'content': content,
            'word_count': word_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'File upload failed: {str(e)}'})

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        raw_text = data.get('text', '')
        max_words = int(data.get('max_words', 150))
        
        if not raw_text.strip():
            return jsonify({'success': False, 'error': 'Please provide text to summarize'})
        
        # Process text
        cleaned = clean_text(raw_text)
        word_count = len(cleaned.split())
        
        if word_count < 20:
            return jsonify({'success': False, 'error': 'Text is too short. Please provide at least 20 words.'})
        
        # Generate summary and extract entities
        summary = generate_summary(cleaned, max_words)
        entities = extract_entities(cleaned)
        
        # Calculate compression ratio
        summary_word_count = len(summary.split())
        compression_ratio = round((1 - summary_word_count / word_count) * 100, 1)
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save to history
        save_to_history(cleaned, summary, entities, word_count, timestamp)
        
        return jsonify({
            'success': True,
            'summary': summary,
            'entities': entities,
            'original_word_count': word_count,
            'summary_word_count': summary_word_count,
            'compression_ratio': compression_ratio,
            'timestamp': timestamp
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'})

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from io import BytesIO
        except ImportError:
            return jsonify({'success': False, 'error': 'PDF generation not available. Please install reportlab: pip install reportlab'})
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add content
        story.append(Paragraph("Summary Report", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated: {data.get('timestamp', '')}", styles['Normal']))
        story.append(Paragraph(f"Original Words: {data.get('original_word_count', 0)}", styles['Normal']))
        story.append(Paragraph(f"Summary Words: {data.get('summary_word_count', 0)}", styles['Normal']))
        story.append(Paragraph(f"Compression: {data.get('compression_ratio', 0)}%", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Summary:", styles['Heading2']))
        story.append(Paragraph(data.get('summary', ''), styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'PDF generation failed: {str(e)}'})

@app.route('/history')
def get_history():
    history = load_history()
    return jsonify(history[-10:])  # Return last 10 summaries

@app.route('/clear-history', methods=['POST'])
def clear_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    return jsonify({'success': True})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)