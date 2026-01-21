import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import openai
import requests
import json

# Optional imports for advanced features
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    HAS_ML_LIBS = True
except ImportError:
    SentenceTransformer = None
    cosine_similarity = None
    np = None
    HAS_ML_LIBS = False

load_dotenv()

class AIService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Initialize OpenAI if available
        if self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
        
        # Initialize sentence transformer for similarity (optional)
        if HAS_ML_LIBS:
            try:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            except:
                self.sentence_model = None
        else:
            self.sentence_model = None
    
    def _get_llm_response(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """Get response from LLM (OpenAI or Gemini)"""
        # Try OpenAI first
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant specialized in resume writing and job applications for Indian students."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"OpenAI error: {e}")
        
        # Fallback to Gemini (REST API)
        if self.gemini_api_key:
            try:
                # Fallback model strategy: Prioritize Stable (1.5-flash) over Preview
                models_to_try = ["gemini-1.5-flash", "gemini-pro", "gemini-3-flash-preview"]
                
                clean_key = self.gemini_api_key.strip()
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }

                last_error = ""

                for model_name in models_to_try:
                    try:
                        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
                        # print(f"Trying model: {model_name}...") # Debug log
                        
                        response = requests.post(
                            f"{api_url}?key={clean_key}", 
                            headers=headers, 
                            json=payload
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if "candidates" in result and result["candidates"]:
                                return result["candidates"][0]["content"]["parts"][0]["text"].strip()
                        else:
                            last_error = f"{response.status_code} - {response.text}"
                            # Continue to next model on failure
                            continue
                            
                    except Exception as e:
                        last_error = str(e)
                        continue
                
                # If we get here, all models failed
                return f"Error from AI Provider (All models failed). Last error: {last_error}"

            except Exception as e:
                print(f"Gemini error: {e}")
        
        # Fallback response if no API available
        return "AI service not configured. Please set OPENAI_API_KEY or GEMINI_API_KEY in environment variables."
    
    def customize_resume(self, resume_data: Dict[str, Any], job_description: Dict[str, Any]) -> Dict[str, Any]:
        """Customize resume based on job description"""
        # Extract key information
        resume_skills = resume_data.get("skills", [])
        resume_projects = resume_data.get("projects", [])
        resume_experience = resume_data.get("experience", [])
        
        jd_skills = job_description.get("required_skills", [])
        jd_keywords = job_description.get("priority_keywords", [])
        jd_tools = job_description.get("tools_technologies", [])
        jd_expectations = job_description.get("role_expectations", "")
        
        # Calculate relevance score
        relevance_score = self._calculate_relevance_score(
            resume_skills, resume_projects, jd_skills, jd_keywords
        )
        
        # Identify missing skills
        missing_skills = [skill for skill in jd_skills if skill.lower() not in [s.lower() for s in resume_skills]]
        
        # Reorder and enhance projects based on relevance
        enhanced_projects = self._enhance_projects(resume_projects, jd_skills, jd_keywords)
        
        # Enhance experience descriptions
        enhanced_experience = self._enhance_experience(resume_experience, jd_skills, jd_keywords)
        
        # Create customized resume data
        customized_data = {
            "skills": self._reorder_skills(resume_skills, jd_skills),
            "projects": enhanced_projects,
            "experience": enhanced_experience,
            "education": resume_data.get("education", {}),
            "summary": self._generate_summary(resume_data, job_description),
            "missing_skills_note": missing_skills[:3] if missing_skills else []
        }
        
        # Track changes
        changes_made = {
            "skills_reordered": True,
            "projects_enhanced": len(enhanced_projects),
            "experience_enhanced": len(enhanced_experience),
            "missing_skills": missing_skills[:5]
        }
        
        return {
            "customized_data": customized_data,
            "changes_made": changes_made,
            "relevance_score": relevance_score
        }
    
    def _calculate_relevance_score(self, resume_skills: List[str], resume_projects: List[Dict],
                                   jd_skills: List[str], jd_keywords: List[str]) -> int:
        """Calculate relevance score (0-100)"""
        if not jd_skills:
            return 50
        
        # Count matching skills
        resume_skills_lower = [s.lower() for s in resume_skills]
        jd_skills_lower = [s.lower() for s in jd_skills]
        
        matching_skills = sum(1 for skill in jd_skills_lower if any(rs in skill or skill in rs for rs in resume_skills_lower))
        
        # Calculate percentage
        score = int((matching_skills / len(jd_skills)) * 100) if jd_skills else 0
        
        # Boost score if keywords match
        if jd_keywords:
            keyword_matches = sum(1 for kw in jd_keywords if any(kw.lower() in rs for rs in resume_skills_lower))
            score += min(keyword_matches * 5, 20)
        
        return min(score, 100)
    
    def _reorder_skills(self, resume_skills: List[str], jd_skills: List[str]) -> List[str]:
        """Reorder skills to prioritize JD-relevant ones"""
        jd_skills_lower = [s.lower() for s in jd_skills]
        relevant_skills = []
        other_skills = []
        
        for skill in resume_skills:
            skill_lower = skill.lower()
            if any(jd_skill in skill_lower or skill_lower in jd_skill for jd_skill in jd_skills_lower):
                relevant_skills.append(skill)
            else:
                other_skills.append(skill)
        
        return relevant_skills + other_skills
    
    def _enhance_projects(self, projects: List[Dict], jd_skills: List[str], jd_keywords: List[str]) -> List[Dict]:
        """Enhance project descriptions with JD-relevant keywords"""
        enhanced = []
        jd_skills_lower = [s.lower() for s in jd_skills]
        jd_keywords_lower = [kw.lower() for kw in jd_keywords]
        
        for project in projects:
            enhanced_project = project.copy()
            description = project.get("description", "")
            
            # Check if project is relevant
            project_text_lower = description.lower()
            relevance = sum(1 for skill in jd_skills_lower if skill in project_text_lower)
            
            # Enhance description if relevant
            if relevance > 0:
                prompt = f"""Rewrite this project description to better match job requirements. 
Keep it concise and professional. Use simple English suitable for Indian students.

Original: {description}

Job-relevant skills: {', '.join(jd_skills[:5])}

Rewritten description (2-3 sentences):"""
                
                enhanced_description = self._get_llm_response(prompt)
                enhanced_project["description"] = enhanced_description
            
            enhanced.append(enhanced_project)
        
        # Sort by relevance
        enhanced.sort(key=lambda p: sum(1 for skill in jd_skills_lower if skill in p.get("description", "").lower()), reverse=True)
        
        return enhanced
    
    def _enhance_experience(self, experience: List[Dict], jd_skills: List[str], jd_keywords: List[str]) -> List[Dict]:
        """Enhance experience descriptions"""
        enhanced = []
        jd_skills_lower = [s.lower() for s in jd_skills]
        
        for exp in experience:
            enhanced_exp = exp.copy()
            description = exp.get("description", "")
            
            # Enhance if relevant
            if any(skill in description.lower() for skill in jd_skills_lower):
                prompt = f"""Rewrite this experience description to highlight relevant skills for the job. 
Keep it professional and concise.

Original: {description}

Job-relevant skills: {', '.join(jd_skills[:5])}

Rewritten description (2-3 sentences):"""
                
                enhanced_description = self._get_llm_response(prompt)
                enhanced_exp["description"] = enhanced_description
            
            enhanced.append(enhanced_exp)
        
        return enhanced
    
    def _generate_summary(self, resume_data: Dict, job_description: Dict) -> str:
        """Generate or enhance resume summary"""
        existing_summary = resume_data.get("summary", "")
        jd_role = job_description.get("role", "")
        jd_skills = job_description.get("required_skills", [])
        
        if existing_summary:
            prompt = f"""Enhance this resume summary to better match the job role. Keep it professional and concise (2-3 sentences).

Current summary: {existing_summary}

Target role: {jd_role}
Key skills needed: {', '.join(jd_skills[:5])}

Enhanced summary:"""
        else:
            skills = resume_data.get("skills", [])[:5]
            experience = resume_data.get("experience", [])
            projects = resume_data.get("projects", [])
            
            prompt = f"""Write a professional resume summary (2-3 sentences) for a student applying to this role.

Target role: {jd_role}
Key skills: {', '.join(skills)}
Experience: {len(experience)} positions
Projects: {len(projects)} projects

Summary:"""
        
        return self._get_llm_response(prompt)
    
    def generate_application_answer(self, question: str, resume_data: Dict, 
                                   job_description: Dict, word_limit: int = 200) -> str:
        """Generate personalized answer for application questions"""
        jd_role = job_description.get("role", "")
        jd_company = job_description.get("company_name", "")
        jd_expectations = job_description.get("role_expectations", "")
        
        resume_skills = resume_data.get("skills", [])[:5]
        resume_projects = resume_data.get("projects", [])[:2]
        
        prompt = f"""Generate a personalized answer for this application question. 
Use simple, professional English suitable for Indian students. Keep it under {word_limit} words.

Question: {question}

Job Role: {jd_role}
Company: {jd_company}
Key Requirements: {jd_expectations[:200]}

My Skills: {', '.join(resume_skills)}
My Projects: {', '.join([p.get('name', '') for p in resume_projects])}

Answer:"""
        
        answer = self._get_llm_response(prompt)
        
        # Ensure word limit
        words = answer.split()
        if len(words) > word_limit:
            answer = ' '.join(words[:word_limit]) + "..."
        
        return answer
    
    def analyze_skill_gaps(self, user_skills: List[str], job_descriptions: List[Dict]) -> Dict[str, Any]:
        """Analyze skill gaps and provide recommendations"""
        # Collect all required skills from JDs
        all_required_skills = []
        for jd in job_descriptions:
            all_required_skills.extend(jd.get("required_skills", []))
            all_required_skills.extend(jd.get("tools_technologies", []))
        
        # Count frequency
        from collections import Counter
        skill_frequency = Counter([s.lower() for s in all_required_skills])
        
        # Find missing skills
        user_skills_lower = [s.lower() for s in user_skills]
        missing_skills = [skill for skill, count in skill_frequency.most_common(20) 
                         if skill not in user_skills_lower]
        
        # Generate recommendations
        recommended_skills = missing_skills[:10]
        
        # Generate project ideas
        project_ideas = []
        for skill in recommended_skills[:5]:
            prompt = f"""Suggest a beginner-friendly project idea for learning {skill}. 
Keep it practical and suitable for Indian students. One sentence only."""
            idea = self._get_llm_response(prompt)
            project_ideas.append(f"{skill.title()}: {idea}")
        
        # Learning resources (hardcoded for now, can be enhanced)
        learning_resources = []
        for skill in recommended_skills[:5]:
            learning_resources.append({
                "skill": skill.title(),
                "resources": [
                    {"name": f"Learn {skill.title()} - YouTube", "url": f"https://youtube.com/results?search_query=learn+{skill}", "type": "free"},
                    {"name": f"{skill.title()} Tutorial - GeeksforGeeks", "url": f"https://geeksforgeeks.org/{skill}", "type": "free"}
                ]
            })
        
        return {
            "missing_skills": missing_skills[:15],
            "recommended_skills": recommended_skills,
            "project_ideas": project_ideas,
            "learning_resources": learning_resources
        }

    def generate_interview_questions(self, resume_data: Dict, job_description: Dict, count: int = 5) -> List[str]:
        """Generate interview questions based on resume and JD"""
        jd_role = job_description.get("role", "")
        jd_company = job_description.get("company_name", "")
        jd_skills = job_description.get("required_skills", [])
        
        resume_skills = resume_data.get("skills", [])
        resume_projects = resume_data.get("projects", [])
        
        prompt = f"""Generate {count} technical and behavioral interview questions for this candidate.
        
        Role: {jd_role} at {jd_company}
        Required Skills: {', '.join(jd_skills)}
        
        Candidate Skills: {', '.join(resume_skills)}
        Candidate Projects: {', '.join([p.get('name', '') for p in resume_projects])}
        
        Output format: Return ONLY the questions as a numbered list.
        """
        
        response = self._get_llm_response(prompt)
        
        # Parse response into list
        questions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove number/bullet
                cleaned = line.lstrip('0123456789.- ').strip()
                if cleaned:
                    questions.append(cleaned)
                    
        return questions

    def evaluate_interview_answer(self, question: str, answer: str, job_description: Dict) -> Dict[str, Any]:
        """Evaluate interview answer"""
        jd_role = job_description.get("role", "")
        jd_skills = job_description.get("required_skills", [])
        
        prompt = f"""Evaluate this interview answer for a {jd_role} position.
        
        Question: {question}
        Answer: {answer}
        
        Context - Required Skills: {', '.join(jd_skills)}
        
        Provide feedback in the following format:
        Score: [0-10]
        Strengths: [Comma separated list]
        Weaknesses: [Comma separated list]
        Improvement Suggestion: [Brief suggestion]
        Sample Better Answer: [A concise better answer]
        """
        
        response = self._get_llm_response(prompt)
        
        # Simple parsing (can be made more robust with JSON output from LLM)
        result = {
            "score": 0,
            "feedback": response,
            "strengths": [],
            "weaknesses": [],
            "suggestion": "",
            "sample_answer": ""
        }
        
        # Attempt to parse structured parts if LLM followed format
        try:
            lines = response.split('\n')
            for line in lines:
                if line.startswith("Score:"):
                    result["score"] = int(float(line.split(":")[1].strip().split('/')[0]))
                elif line.startswith("Strengths:"):
                    result["strengths"] = [s.strip() for s in line.split(":")[1].split(',')]
                elif line.startswith("Weaknesses:"):
                    result["weaknesses"] = [s.strip() for s in line.split(":")[1].split(',')]
                elif line.startswith("Improvement Suggestion:"):
                    result["suggestion"] = line.split(":")[1].strip()
        except:
            pass
            
        return result

