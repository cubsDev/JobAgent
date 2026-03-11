import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

def tailor_cv(master_cv: str, job_description: str, job_title: str) -> str:
    """Uses Google Gemini to tailor the master CV to the job description."""
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key or api_key == "your_key_here":
        logger.error("GOOGLE_API_KEY is missing or invalid.")
        return "Error: Google API Key not configured."
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        system_instruction = (
            "You are an expert CV writer for legal tech and EU regulation roles. "
            "Your task is to tailor the provided Master CV to match the Job Description perfectly. "
            "Do not fabricate any experience or add skills the candidate does not have in their Master CV. "
            "Instead, highlight and rephrase their existing experience to mirror the exact keywords in the Job Description. "
            "Output your response cleanly in Markdown format."
        )
        
        prompt = f"""
        {system_instruction}
        
        Job Title: {job_title}
        
        Job Description:
        {job_description}
        
        Master CV:
        {master_cv}
        """
        
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text
        else:
            return "Error: Received empty response from Gemini."
            
    except Exception as e:
        logger.error(f"Error during CV tailoring: {str(e)}")
        return f"Error occurred during CV tailoring: {str(e)}"
