import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

def score_job(job_description: str, cv_summary: str) -> dict:
    api_key = os.environ.get("GOOGLE_API_KEY")
    default_result = {"score": 0, "reason": "Failed to score job (Gemini)", "missing_skills": []}

    if not api_key:
        logger.error("GOOGLE_API_KEY is not set. Cannot use Gemini scorer.")
        default_result["reason"] = "Missing GOOGLE_API_KEY"
        return default_result

    try:
        genai.configure(api_key=api_key)
        # Using gemini-2.5-flash as it's typically faster and cheaper for these tasks
        model = genai.GenerativeModel('gemini-2.5-flash')
        
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
        
        # We can enforce JSON output if the model supports it, but simple text prompting 
        # usually works fine if we strip backticks.
        response = model.generate_content(prompt)
        reply_text = response.text.strip()
        
        # Clean up potential markdown blocks
        if reply_text.startswith("```json"):
            reply_text = reply_text[7:]
        if reply_text.endswith("```"):
            reply_text = reply_text[:-3]
        reply_text = reply_text.strip()
            
        parsed_result = json.loads(reply_text)
        
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
        logger.error(f"Failed to parse Gemini JSON response: {je}. Raw: {reply_text}")
        return default_result
    except Exception as e:
        logger.error(f"Error during Gemini scoring: {str(e)}")
        return default_result
