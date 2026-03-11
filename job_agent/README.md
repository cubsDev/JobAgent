# JobSearch Agent

An automated job search and CV tailoring agent built with Python Flask, JobSpy, Ollama, and Google Generative AI.

## Project Structure
- `app.py`: Flask application factory and routes.
- `models.py`: Database definitions using SQLAlchemy.
- `config.py`: Environment variable loading.
- `scheduler.py`: Background task scheduling using APScheduler.
- `agents/`: Core backend logic files
  - `scraper.py`: Uses JobSpy to scrape Google, Indeed, and LinkedIn.
  - `scorer.py`: Post JobDescription and Master CV to a local Ollama reasoning model (`qwen2.5:7b`).
  - `tailor.py`: Connects to `gemini-2.5-flash` to tailor the CV.
- `templates/`: Jinja2 templates using TailwindCSS via CDN.
  - `base.html`, `index.html`, `job_detail.html`, `settings.html`
- `master_cv.txt`: Your base CV to feed to the models.

## Setup Instructions

1. **Install Dependencies**
   Make sure you have Python 3.9+ installed.
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   Modify `.env` to include your specific variables:
   ```env
   GOOGLE_API_KEY=your_key_here
   FLASK_SECRET_KEY=change_me
   OLLAMA_BASE_URL=http://localhost:11434
   ```

3. **Install and Run Ollama**
   Ensure Ollama is running locally on port 11434. Pull the `qwen2.5:7b` model:
   ```bash
   ollama pull qwen2.5:7b
   ```

4. **Initialize and Run the Application**
   Run the Flask server from the terminal:
   ```bash
   flask run
   ```
   Or:
   ```bash
   python app.py
   ```

5. **Using the Application**
   - Access the dashboard at `http://localhost:5000/`
   - Go to **Settings** first. Paste your Master CV and fill out your search constraints.
   - Click **Run Now** in the top navigation to trigger a manual pipeline run.
   - Background runs are scheduled automatically daily at 08:00 AM.
   - For jobs that pass your threshold, review them and click **Tailor CV** to trigger the Gemini tailoring.
   - Click **Export .docx** to download a customized CV based on your specific skills.
