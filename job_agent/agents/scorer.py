import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

def score_job(job_description: str, cv_summary: str) -> dict:
    ollama_base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    url = f"{ollama_base_url}/api/generate"
    
    prompt = f"""
    You are an expert HR recruiter evaluating a job description against a candidate's CV summary.
    Score how well the candidate fits the job from 1 to 10 (10 being perfect match).
    You MUST return ONLY valid JSON and nothing else. Do not use Markdown formatting for the JSON.
    Format your response EXACTLY like this:
    {{"score": 8, "reason": "Short reason here", "missing_skills": ["skill1", "skill2"]}}
    
    Candidate CV Summary:
    {cv_summary}
    
    Job Description:
    {job_description}
    """
    
    ollama_model = os.environ.get('OLLAMA_MODEL', 'qwen2.5:7b')
    
    payload = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": False
    }
    
    default_result = {"score": 0, "reason": "Failed to score job", "missing_skills": []}

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        reply_text = response.json().get('response', '').strip()
        
        # Strip potential markdown formatting that local models sometimes add
        if reply_text.startswith("```json"):
            reply_text = reply_text[7:]
        if reply_text.endswith("```"):
            reply_text = reply_text[:-3]
        reply_text = reply_text.strip()
            
        parsed_result = json.loads(reply_text)
        
        # Ensure correct types format
        score = int(parsed_result.get("score", 0))
        reason = str(parsed_result.get("reason", ""))
        missing_skills = parsed_result.get("missing_skills", [])
        if not isinstance(missing_skills, list):
            missing_skills = []
            
        return {
            "score": score,
            "reason": reason,
            "missing_skills": missing_skills
        }
        
    except json.JSONDecodeError as je:
        logger.error(f"Failed to parse Ollama JSON response: {je}. Raw: {reply_text}")
        return default_result
    except Exception as e:
        logger.error(f"Error during Ollama scoring: {str(e)}")
        return default_result
