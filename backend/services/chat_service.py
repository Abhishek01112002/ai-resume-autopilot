import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class ChatService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    async def get_chat_response(self, message: str, context: str = "") -> str:
        if not self.api_key:
             return "Error: Gemini API key not configured. Please add GEMINI_API_KEY to your .env file."
        
        try:
            # Construct a prompt that guides the AI
            system_prompt = """You are an expert Career Coach and Resume Assistant named 'ResumAI Bot'. 
            Your goal is to help users with:
            1. Resume improvements and ATS optimization.
            2. Job search strategies and internship advice.
            3. Interview preparation and career guidance.
            4. Real-life work situations.
            
            Keep your answers concise, encouraging, and actionable. 
            If the user asks about specific resume details, ask them to upload or refer to their uploaded resume.
            """
            
            # Fallback model strategy: Prioritize Stable (1.5-flash) over Preview
            models_to_try = ["gemini-1.5-flash", "gemini-pro", "gemini-3-flash-preview"]
            
            clean_key = self.api_key.strip()
            headers = {"Content-Type": "application/json"}
            
            full_prompt = f"{system_prompt}\n\nContext: {context}\n\nUser Query: {message}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }]
            }
            
            last_error = ""

            for model_name in models_to_try:
                try:
                    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
                    
                    response = requests.post(
                        f"{api_url}?key={clean_key}",
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "candidates" in result and result["candidates"]:
                            return result["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        last_error = f"{response.status_code} - {response.text}"
                        continue
                        
                except Exception as e:
                    last_error = str(e)
                    continue

            return f"Error from AI Provider (All models failed). Last error: {last_error}"
                
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"

chat_service = ChatService()
