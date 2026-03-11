import sys
from jobspy import scrape_jobs

def test_scrape(location):
    print(f"Testing JobSpy for: {location}")
    try:
        jobs = scrape_jobs(
            site_name=["linkedin", "indeed", "google"],
            search_term="Software Engineer",
            location=location,
            results_wanted=5,
            hours_old=72,
            country_indeed='ireland' if 'ireland' in location.lower() else 'netherlands'
        )
        if jobs is None or jobs.empty:
            print(f"No results found for {location}.")
        else:
            print(f"Found {len(jobs)} jobs for {location}.")
            for index, job in jobs.head(3).iterrows():
                print(f"- {job.get('title')} at {job.get('company')} ({job.get('location')})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_scrape("Dublin, Ireland")
    test_scrape("Amsterdam, Netherlands")
