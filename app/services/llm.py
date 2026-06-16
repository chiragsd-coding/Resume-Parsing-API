"""LLM integration - Ollama for interview generation and AI copilot."""
import httpx
import logging
from typing import Optional, AsyncGenerator
import json

logger = logging.getLogger(__name__)

class OllamaService:
    """Interface with local Ollama LLM."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def generate(self, prompt: str, temperature: float = 0.7, 
                      max_tokens: int = 2048) -> str:
        """Generate text from prompt."""
        try:
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stream": False
                }
            )
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    async def stream_generate(self, prompt: str, 
                             temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """Stream text generation."""
        try:
            async with self.client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        yield data.get("response", "")
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except:
            return False

class InterviewQuestionGenerator:
    """Generate interview questions using LLM."""
    
    def __init__(self, llm: OllamaService):
        self.llm = llm
    
    async def generate_questions(self,
                                job_title: str,
                                required_skills: list,
                                experience_level: str,
                                num_questions: int = 5) -> list:
        """Generate interview questions."""
        
        prompt = f"""You are an expert interviewer. Generate {num_questions} interview questions for a {experience_level} level {job_title} position.
        
Required skills: {', '.join(required_skills)}

Generate questions in this JSON format:
{{
    "questions": [
        {{
            "question": "question text",
            "type": "technical/behavioral/situational",
            "difficulty": "easy/medium/hard",
            "expected_areas": ["area1", "area2"]
        }}
    ]
}}

Ensure questions are:
- Role-appropriate
- Mix of technical and behavioral
- Progressively challenging
- Open-ended for discussion

Response must be valid JSON only."""
        
        try:
            response = await self.llm.generate(prompt)
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("questions", [])
            return []
        except Exception as e:
            logger.error(f"Question generation error: {e}")
            return []

class InterviewEvaluator:
    """Evaluate interview answers using LLM."""
    
    def __init__(self, llm: OllamaService):
        self.llm = llm
    
    async def evaluate_answer(self,
                             question: str,
                             candidate_answer: str,
                             role: str) -> dict:
        """Evaluate interview answer."""
        
        prompt = f"""Evaluate this interview answer for a {role} position.

Question: {question}

Candidate's Answer: {candidate_answer}

Provide evaluation in JSON format:
{{
    "score": 0-10,
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "feedback": "constructive feedback",
    "follow_up_question": "suggested follow-up question",
    "sentiment": "positive/neutral/negative"
}}

Response must be valid JSON only."""
        
        try:
            response = await self.llm.generate(prompt)
            import re
            import json
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"score": 5, "feedback": "Unable to evaluate"}
        except Exception as e:
            logger.error(f"Answer evaluation error: {e}")
            return {"score": 0, "feedback": str(e)}

class RecruiterCopilot:
    """AI-powered recruiter assistant."""
    
    def __init__(self, llm: OllamaService):
        self.llm = llm
    
    async def analyze_candidate(self,
                               candidate_profile: dict,
                               job_description: dict) -> dict:
        """Analyze candidate fit for role."""
        
        prompt = f"""Analyze this candidate for the role:

Candidate:
- Skills: {', '.join(candidate_profile.get('skills', []))}
- Experience: {candidate_profile.get('summary', '')}

Job Requirements:
- Title: {job_description.get('job_title')}
- Skills: {', '.join(job_description.get('required_skills', []))}
- Level: {job_description.get('experience_level')}

Provide analysis:
{{
    "recommendation": "strong_match/good_match/fair_match/poor_match",
    "fit_summary": "2-3 sentence summary",
    "strengths": ["strength1", "strength2", "strength3"],
    "concerns": ["concern1", "concern2"],
    "talking_points": ["point1", "point2"],
    "next_steps": ["step1", "step2"]
}}

Response must be valid JSON only."""
        
        try:
            response = await self.llm.generate(prompt)
            import re
            import json
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"recommendation": "fair_match"}
        except Exception as e:
            logger.error(f"Candidate analysis error: {e}")
            return {"recommendation": "unable_to_analyze", "error": str(e)}
    
    async def generate_job_description(self, role_details: dict) -> str:
        """Generate JD from role details."""
        
        prompt = f"""Generate a professional job description:

Role: {role_details.get('title')}
Level: {role_details.get('level')}
Key Skills: {', '.join(role_details.get('key_skills', []))}
Responsibilities: {role_details.get('responsibilities', '')}

Generate a complete, professional job description with:
- Summary
- Key Responsibilities
- Required Qualifications
- Nice-to-Have Skills
- Compensation Info
- Benefits

Make it compelling for candidates."""
        
        return await self.llm.generate(prompt)
    
    async def generate_rejection_email(self, candidate_name: str, 
                                      reason: str) -> str:
        """Generate professional rejection email."""
        
        prompt = f"""Generate a professional rejection email for {candidate_name}.

Rejection reason: {reason}

The email should be:
- Professional and respectful
- Constructive feedback
- Encouraging for future opportunities
- 2-3 paragraphs

Do not include email headers."""
        
        return await self.llm.generate(prompt)
