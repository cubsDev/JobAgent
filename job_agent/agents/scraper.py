import logging
from jobspy import scrape_jobs
from models import JobPost

logger = logging.getLogger(__name__)

def run_scrape(search_term: str, location: str, results_wanted: int, hours_old: int) -> list[dict]:
    try:
        # Determine country_indeed for JobSpy based on location
        loc_lower = location.lower()
        country_indeed = 'usa'
        if 'ireland' in loc_lower or 'ie' in loc_lower:
            country_indeed = 'ireland'
        elif 'uk' in loc_lower or 'united kingdom' in loc_lower or 'england' in loc_lower or 'london' in loc_lower:
            country_indeed = 'uk'
        elif 'canada' in loc_lower:
            country_indeed = 'canada'
        elif 'australia' in loc_lower:
            country_indeed = 'australia'
        elif 'netherlands' in loc_lower:
            country_indeed = 'netherlands'
            
        # Use JobSpy to scrape
        jobs = scrape_jobs(
            site_name=["linkedin", "indeed", "google"],
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed=country_indeed
        )
        
        if jobs is None or jobs.empty:
            logger.info(f"No jobs found for {search_term} in {location}")
            return []
            
        # Convert pandas dataframe to list of dicts
        scraped_jobs = jobs.to_dict(orient='records')
        new_jobs = []
        seen_urls = set()
        
        for job in scraped_jobs:
            url = str(job.get('job_url', ''))
            if not url or url in seen_urls:
                continue
                
            seen_urls.add(url)
            
            # Check if job already exists by URL
            existing = JobPost.query.filter_by(url=url).first()
            if not existing:
                new_jobs.append({
                    'title': str(job.get('title', 'Unknown Title')),
                    'company': str(job.get('company', 'Unknown Company')),
                    'location': str(job.get('location', location)),
                    'url': url,
                    'description': str(job.get('description', '')),
                    'source': str(job.get('site', 'unknown'))
                })
        
        logger.info(f"Scrape completed: {len(scraped_jobs)} raw, {len(new_jobs)} new.")
        return new_jobs
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        return []
