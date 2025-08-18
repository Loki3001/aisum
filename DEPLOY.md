# AI Summarizer - Render Deployment Guide

## Quick Deploy to Render

### Method 1: Deploy from GitHub (Recommended)

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/ai-summarizer.git
   git push -u origin main
   ```

2. **Deploy on Render:**
   - Go to [render.com](https://render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Use these settings:
     - **Name**: ai-summarizer
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
     - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
     - **Instance Type**: Free

### Method 2: Deploy using render.yaml

1. Push your code to GitHub (including the `render.yaml` file)
2. Go to Render dashboard
3. Click "New" → "Blueprint"
4. Connect your repository
5. Render will automatically use the `render.yaml` configuration

### Environment Variables (Optional)

If you want to add any environment variables:
- `FLASK_ENV=production`
- `PYTHON_VERSION=3.10.0`

### Important Notes

- The free tier on Render may have limitations with large ML models
- Initial deployment may take 10-15 minutes due to PyTorch installation
- The service will sleep after 15 minutes of inactivity on free tier
- For production use, consider upgrading to a paid plan

### Troubleshooting

1. **Build fails due to PyTorch**: The app includes fallback summarization
2. **spaCy model not found**: The build command downloads it automatically  
3. **Memory issues**: Consider using the CPU-only version of PyTorch

### Features Available

- ✅ Text summarization (with AI models when available)
- ✅ Fallback extractive summarization
- ✅ Entity extraction
- ✅ File upload (TXT, DOCX)
- ✅ PDF report generation
- ✅ Summary history
- ✅ Responsive web interface
