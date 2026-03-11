from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class JobPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(1024), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(50), nullable=False)
    relevance_score = db.Column(db.Integer, nullable=True)
    score_reason = db.Column(db.Text, nullable=True)
    missing_skills = db.Column(db.Text, nullable=True) # JSON array as string
    tailored_cv_md = db.Column(db.Text, nullable=True)
    docx_path = db.Column(db.String(1024), nullable=True)
    status = db.Column(db.String(50), default='new', nullable=False) # new/reviewed/applied/rejected
    scraped_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<JobPost {self.title} at {self.company}>'

class SearchConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    search_term = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    results_wanted = db.Column(db.Integer, default=30)
    hours_old = db.Column(db.Integer, default=72)
    score_threshold = db.Column(db.Integer, default=7)
    scoring_engine = db.Column(db.String(50), default='ollama') # ollama, gemini, keyword, none
    keywords = db.Column(db.String(1024), default="")
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<SearchConfig {self.search_term} in {self.location}>'
