"""Candidate-to-job matching engine with vector search."""
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class MatchingEngine:
    """Vector-based semantic matching between candidates and jobs."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding model."""
        self.model = SentenceTransformer(model_name)
    
    async def match_candidate_to_job(self, 
                                    candidate_skills: List[str],
                                    candidate_experience: List[str],
                                    job_required_skills: List[str],
                                    job_nice_to_have: List[str]) -> Dict:
        """Calculate match score between candidate and job."""
        
        # Calculate skill match
        skill_score = self._calculate_skill_match(
            candidate_skills,
            job_required_skills,
            job_nice_to_have
        )
        
        # Calculate experience match
        exp_score = self._calculate_experience_match(
            candidate_experience,
            job_required_skills
        )
        
        # Calculate semantic similarity
        semantic_score = await self._calculate_semantic_match(
            candidate_skills + candidate_experience,
            job_required_skills + job_nice_to_have
        )
        
        # Weighted overall score
        overall_score = (skill_score * 0.5 + exp_score * 0.3 + semantic_score * 0.2) * 100
        
        return {
            "overall_score": round(overall_score, 2),
            "skill_match_score": round(skill_score * 100, 2),
            "experience_match_score": round(exp_score * 100, 2),
            "semantic_match_score": round(semantic_score * 100, 2),
        }
    
    def _calculate_skill_match(self, 
                               candidate_skills: List[str],
                               required_skills: List[str],
                               nice_to_have: List[str]) -> float:
        """Calculate skill match score (0-1)."""
        if not required_skills:
            return 0.0
        
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        required_lower = [s.lower() for s in required_skills]
        nice_lower = [s.lower() for s in nice_to_have]
        
        # Exact matches
        required_matches = sum(1 for s in required_lower if s in candidate_skills_lower)
        nice_matches = sum(1 for s in nice_lower if s in candidate_skills_lower)
        
        # Calculate score
        required_score = required_matches / len(required_skills) if required_skills else 0
        nice_score = (nice_matches / len(nice_lower)) * 0.3 if nice_lower else 0
        
        return min(1.0, required_score + nice_score)
    
    def _calculate_experience_match(self,
                                   candidate_experience: List[str],
                                   job_skills: List[str]) -> float:
        """Calculate experience relevance score."""
        if not candidate_experience or not job_skills:
            return 0.5
        
        # Simple heuristic: check for skill mentions in experience
        exp_text = " ".join(candidate_experience).lower()
        matches = sum(1 for skill in job_skills if skill.lower() in exp_text)
        
        return min(1.0, matches / len(job_skills)) if job_skills else 0.5
    
    async def _calculate_semantic_match(self,
                                       candidate_tokens: List[str],
                                       job_tokens: List[str]) -> float:
        """Calculate semantic similarity using embeddings."""
        try:
            candidate_text = " ".join(candidate_tokens)
            job_text = " ".join(job_tokens)
            
            # Generate embeddings
            candidate_embedding = self.model.encode(candidate_text)
            job_embedding = self.model.encode(job_text)
            
            # Calculate cosine similarity
            similarity = np.dot(candidate_embedding, job_embedding) / (
                np.linalg.norm(candidate_embedding) * np.linalg.norm(job_embedding)
            )
            
            return max(0, min(1, (similarity + 1) / 2))  # Normalize to 0-1
        except Exception as e:
            logger.error(f"Semantic matching error: {e}")
            return 0.5

class SkillGapAnalyzer:
    """Analyze skill gaps between candidate and job."""
    
    @staticmethod
    def analyze_gaps(candidate_skills: List[str],
                    required_skills: List[str],
                    nice_to_have: List[str]) -> Dict:
        """Identify skill gaps and provide recommendations."""
        
        candidate_lower = {s.lower(): s for s in candidate_skills}
        
        # Find gaps
        gaps = []
        for skill in required_skills:
            if skill.lower() not in candidate_lower:
                gaps.append({
                    "skill": skill,
                    "type": "required",
                    "priority": "high"
                })
        
        # Nice-to-have gaps
        nice_gaps = []
        for skill in nice_to_have:
            if skill.lower() not in candidate_lower:
                nice_gaps.append({
                    "skill": skill,
                    "type": "nice_to_have",
                    "priority": "medium"
                })
        
        # Find surplus skills
        job_skills_lower = {s.lower() for s in required_skills + nice_to_have}
        surplus = [
            s for s in candidate_skills 
            if s.lower() not in job_skills_lower
        ]
        
        # Recommendations
        recommendations = SkillGapAnalyzer._generate_recommendations(gaps, nice_gaps)
        
        return {
            "critical_gaps": gaps,
            "nice_to_have_gaps": nice_gaps,
            "surplus_skills": surplus,
            "gap_count": len(gaps),
            "recommendations": recommendations
        }
    
    @staticmethod
    def _generate_recommendations(gaps: List[Dict], nice_gaps: List[Dict]) -> List[Dict]:
        """Generate learning recommendations."""
        recommendations = []
        
        # Prioritize critical gaps
        for gap in gaps[:3]:  # Top 3 critical gaps
            recommendations.append({
                "skill": gap["skill"],
                "priority": "high",
                "resources": [
                    {"type": "course", "platform": "Udemy"},
                    {"type": "certification", "platform": "Coursera"},
                    {"type": "practice", "platform": "LeetCode/HackerRank"}
                ]
            })
        
        # Add nice-to-haves
        for gap in nice_gaps[:2]:  # Top 2 nice-to-haves
            recommendations.append({
                "skill": gap["skill"],
                "priority": "medium",
                "resources": [{"type": "tutorial", "platform": "YouTube"}]
            })
        
        return recommendations

class DuplicateDetector:
    """Detect duplicate candidates using embeddings."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    async def find_duplicates(self, 
                             candidate_name: str,
                             candidate_email: str,
                             candidate_phone: str,
                             existing_candidates: List[Dict],
                             threshold: float = 0.85) -> List[Dict]:
        """Find potential duplicate candidates."""
        
        candidates_embedding = self.model.encode(f"{candidate_name} {candidate_email} {candidate_phone}")
        duplicates = []
        
        for existing in existing_candidates:
            existing_embedding = self.model.encode(
                f"{existing.get('name', '')} {existing.get('email', '')} {existing.get('phone', '')}"
            )
            
            # Calculate similarity
            similarity = np.dot(candidates_embedding, existing_embedding) / (
                np.linalg.norm(candidates_embedding) * np.linalg.norm(existing_embedding)
            )
            
            if similarity >= threshold:
                duplicates.append({
                    "candidate_id": existing.get("id"),
                    "similarity_score": round(similarity, 3),
                    "conflict_reason": self._get_conflict_reason(
                        candidate_name, existing.get("name"),
                        candidate_email, existing.get("email")
                    )
                })
        
        return sorted(duplicates, key=lambda x: x["similarity_score"], reverse=True)
    
    @staticmethod
    def _get_conflict_reason(name1: str, name2: str, email1: str, email2: str) -> str:
        """Identify why records are considered duplicates."""
        reasons = []
        if name1.lower() == name2.lower():
            reasons.append("same_name")
        if email1.lower() == email2.lower():
            reasons.append("same_email")
        if not reasons:
            reasons.append("similar_profile")
        return ", ".join(reasons)
