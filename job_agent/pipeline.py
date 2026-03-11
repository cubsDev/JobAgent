import logging
import json
from models import db, SearchConfig, JobPost
from agents.scraper import run_scrape
from agents.scorer import score_job as ollama_score_job
from agents.gemini_scorer import score_job as gemini_score_job

logger = logging.getLogger(__name__)

# Global state for the frontend status bar
pipeline_state = {
    "is_running": False,
    "message": "Idle",
    "progress": 0,
    "total": 0
}

def load_master_cv():
    import os
    cv_path = os.path.join(os.path.dirname(__file__), 'master_cv.txt')
    if os.path.exists(cv_path):
        with open(cv_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def run_pipeline(app):
    global pipeline_state
    pipeline_state["is_running"] = True
    pipeline_state["message"] = "Starting pipeline..."
    pipeline_state["progress"] = 0
    pipeline_state["total"] = 0
    logger.info("Starting automated job pipeline...")
        
    with app.app_context():
        # 1. Load active SearchConfig
        active_configs = SearchConfig.query.filter_by(is_active=True).all()
        if not active_configs:
            logger.info("No active SearchConfig found. Skipping pipeline.")
            pipeline_state["is_running"] = False
            pipeline_state["message"] = "Idle"
            return
            
        # 2. Load master_cv.txt content summary (first 1000 chars)
        master_cv = load_master_cv()
        cv_summary = master_cv[:1000] if master_cv else "No CV provided."
        
        for config in active_configs:
            # 3. Scrape for each selected location
            new_jobs = []
            seen_pipeline_urls = set()
            locations = [loc.strip() for loc in config.location.split('|') if loc.strip()]
            
            for loc in locations:
                pipeline_state["message"] = f"Scraping jobs in {loc}..."
                logger.info(f"Running scrape for '{config.search_term}' in '{loc}'")
                scraped_for_loc = run_scrape(
                    search_term=config.search_term,
                    location=loc,
                    results_wanted=config.results_wanted,
                    hours_old=config.hours_old
                )
                
                # Deduplicate jobs that appear in multiple cities before commit
                for job in scraped_for_loc:
                    if job['url'] not in seen_pipeline_urls:
                        seen_pipeline_urls.add(job['url'])
                        new_jobs.append(job)
            
            jobs_above_threshold = 0
            pipeline_state["total"] = len(new_jobs)
            
            # 4. Score or Match new jobs
            for idx, job_data in enumerate(new_jobs):
                pipeline_state["progress"] = idx + 1
                pipeline_state["message"] = f"Evaluating job: {job_data.get('title')} ({idx+1}/{len(new_jobs)})"
                
                job_title = str(job_data.get('title', ''))
                job_desc = str(job_data.get('description', ''))
                
                score = 0
                reason = ""
                missing_skills = []
                engine = config.scoring_engine or 'ollama'

                # BRANCH A: Keyword Matcher
                if engine == 'keyword':
                    logger.info(f"Keyword matching job: {job_title}")
                    search_keywords = [k.strip().lower() for k in (config.keywords or '').split(',') if k.strip()]

                    title_lower = job_title.lower()
                    desc_lower = job_desc.lower()

                    matched_in_title = [kw for kw in search_keywords if kw in title_lower]
                    matched_in_desc = [kw for kw in search_keywords if kw in desc_lower and kw not in matched_in_title]

                    if matched_in_title:
                        score = 10
                        all_matches = matched_in_title + matched_in_desc
                        reason = f"Keyword in Title: {', '.join(all_matches)}"
                    elif matched_in_desc:
                        score = 5
                        reason = f"Keyword in Description: {', '.join(matched_in_desc)}"
                    else:
                        score = 0
                        reason = "No keywords matched"

                # BRANCH B: Ollama AI Scoring
                elif engine == 'ollama':
                    logger.info(f"Ollama scoring job: {job_title} at {job_data.get('company')}")
                    score_result = ollama_score_job(job_desc, cv_summary)
                    score = score_result.get('score', 0)
                    reason = score_result.get('reason', '')
                    missing_skills = score_result.get('missing_skills', [])

                # BRANCH C: Gemini AI Scoring
                elif engine == 'gemini':
                    logger.info(f"Gemini scoring job: {job_title} at {job_data.get('company')}")
                    score_result = gemini_score_job(job_desc, cv_summary)
                    score = score_result.get('score', 0)
                    reason = score_result.get('reason', '')
                    missing_skills = score_result.get('missing_skills', [])

                # BRANCH D: No Filtering — save everything
                elif engine == 'none':
                    logger.info(f"No filtering — saving job: {job_title}")
                    score = 10
                    reason = "No filtering applied"

                # Threshold Check & Save
                if engine in ('keyword', 'none') or score >= config.score_threshold:
                    jobs_above_threshold += 1
                    job_post = JobPost(
                        title=job_data.get('title'),
                        company=job_data.get('company'),
                        location=job_data.get('location'),
                        url=job_data.get('url'),
                        description=job_data.get('description'),
                        source=job_data.get('source'),
                        relevance_score=score,
                        score_reason=reason,
                        missing_skills=json.dumps(missing_skills)
                    )
                    db.session.add(job_post)
            
            # 5. Commit changes
            pipeline_state["message"] = "Saving results to database..."
            try:
                db.session.commit()
                logger.info(f"Pipeline finished for '{config.search_term}'. Scraped {len(new_jobs)} new jobs, {jobs_above_threshold} above threshold.")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to commit new jobs to database: {e}")

    pipeline_state["is_running"] = False
    pipeline_state["message"] = "Pipeline finished!"

