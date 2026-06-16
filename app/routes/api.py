"""Main API routes - resumes, JDs, matching, billing."""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import asyncio

from app.database import get_db
from app.auth import get_current_user, get_current_tenant, AuthService, RBACService
from app.models.base import (
    Resume, JobDescription, CandidateMatch, Candidate, 
    AuditLog, AuditAction, ApiKey
)
from app.services.parser import ResumeParser, JDParser
from app.services.matching import MatchingEngine, SkillGapAnalyzer, DuplicateDetector
from app.services.llm import (
    OllamaService, InterviewQuestionGenerator, 
    InterviewEvaluator, RecruiterCopilot
)
from app.services.billing import BillingService, UsageMeter
from app.config import settings

router = APIRouter(prefix="/api/v1")

# Initialize services
resume_parser = ResumeParser()
jd_parser = JDParser()
matching_engine = MatchingEngine()
duplicate_detector = DuplicateDetector()
skill_gap_analyzer = SkillGapAnalyzer()

llm = OllamaService(settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL)
question_generator = InterviewQuestionGenerator(llm)
answer_evaluator = InterviewEvaluator(llm)
recruiter_copilot = RecruiterCopilot(llm)

billing_service = BillingService(settings.STRIPE_SECRET_KEY)
usage_meter = UsageMeter()

# RESUME ENDPOINTS

@router.post("/resumes/parse")
async def parse_resume(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Parse resume and extract data."""
    
    # Check quota
    has_quota, quota_info = await usage_meter.check_quota(
        tenant_id, "resume_parsing", "monthly"
    )
    if not has_quota:
        raise HTTPException(status_code=429, detail="Monthly quota exceeded")
    
    try:
        # Save file
        file_path = f"./uploads/{tenant_id}/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Parse
        parsed_data = await resume_parser.parse_resume(file_path)
        
        # Store in DB
        resume = Resume(
            tenant_id=tenant_id,
            file_name=file.filename,
            file_path=file_path,
            raw_text=parsed_data.get("raw_text"),
            parsed_data=parsed_data,
            full_name=parsed_data.get("full_name"),
            email=parsed_data.get("email"),
            phone=parsed_data.get("phone"),
            location=parsed_data.get("location"),
            summary=parsed_data.get("summary"),
            skills=parsed_data.get("skills", []),
            experience=parsed_data.get("experience", []),
            education=parsed_data.get("education", []),
            certifications=parsed_data.get("certifications", [])
        )
        db.add(resume)
        db.commit()
        
        # Record usage
        await usage_meter.record_usage(db, tenant_id, "resume_parsed", 1, 0.50)
        
        # Audit log
        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user["user_id"],
            action=AuditAction.CREATE,
            resource_type="resume",
            resource_id=resume.id
        )
        db.add(audit)
        db.commit()
        
        return {
            "resume_id": resume.id,
            "parsed_data": parsed_data,
            "quota_remaining": quota_info["remaining"]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/resumes/{resume_id}")
async def get_resume(
    resume_id: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get resume details."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.tenant_id == tenant_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "full_name": resume.full_name,
        "email": resume.email,
        "phone": resume.phone,
        "location": resume.location,
        "skills": resume.skills,
        "experience": resume.experience,
        "education": resume.education,
        "parsed_data": resume.parsed_data
    }

@router.post("/resumes/bulk-upload")
async def bulk_upload_resumes(
    files: List[UploadFile] = File(...),
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Bulk upload and parse multiple resumes."""
    
    results = []
    for file in files:
        try:
            # Simplified bulk processing
            file_path = f"./uploads/{tenant_id}/{file.filename}"
            with open(file_path, "wb") as f:
                f.write(await file.read())
            
            parsed_data = await resume_parser.parse_resume(file_path)
            
            resume = Resume(
                tenant_id=tenant_id,
                file_name=file.filename,
                file_path=file_path,
                parsed_data=parsed_data,
                full_name=parsed_data.get("full_name")
            )
            db.add(resume)
            db.commit()
            
            results.append({
                "file": file.filename,
                "status": "success",
                "resume_id": resume.id
            })
        except Exception as e:
            results.append({
                "file": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    return {"results": results, "total": len(files), "success": len([r for r in results if r["status"] == "success"])}

# JOB DESCRIPTION ENDPOINTS

@router.post("/job-descriptions")
async def create_job_description(
    job_data: dict,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Create/parse job description."""
    
    parsed_data = await jd_parser.parse_jd(job_data.get("description", ""))
    
    jd = JobDescription(
        tenant_id=tenant_id,
        job_title=parsed_data.get("job_title") or job_data.get("job_title"),
        company_name=job_data.get("company_name"),
        job_description=job_data.get("description"),
        parsed_data=parsed_data,
        required_skills=parsed_data.get("required_skills", []),
        nice_to_have_skills=parsed_data.get("nice_to_have_skills", []),
        experience_level=parsed_data.get("experience_level"),
        years_experience_required=parsed_data.get("years_experience")
    )
    db.add(jd)
    db.commit()
    
    return {
        "id": jd.id,
        "job_title": jd.job_title,
        "parsed_data": parsed_data
    }

# MATCHING ENDPOINTS

@router.post("/matches/search")
async def search_candidates(
    job_id: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Find best matching candidates for a job."""
    
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id,
        JobDescription.tenant_id == tenant_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get all candidates
    candidates = db.query(Candidate).filter(
        Candidate.tenant_id == tenant_id
    ).all()
    
    matches = []
    for candidate in candidates:
        resumes = db.query(Resume).filter(Resume.candidate_id == candidate.id).all()
        if resumes:
            latest_resume = max(resumes, key=lambda r: r.created_at)
            
            match_result = await matching_engine.match_candidate_to_job(
                latest_resume.skills,
                latest_resume.experience,
                job.required_skills,
                job.nice_to_have_skills
            )
            
            match = CandidateMatch(
                candidate_id=candidate.id,
                job_description_id=job_id,
                overall_score=match_result["overall_score"],
                skill_match_score=match_result["skill_match_score"],
                experience_match_score=match_result["experience_match_score"]
            )
            db.add(match)
            
            matches.append({
                "candidate_id": candidate.id,
                "name": candidate.full_name,
                "email": candidate.email,
                **match_result
            })
    
    db.commit()
    
    # Sort by overall score
    matches = sorted(matches, key=lambda x: x["overall_score"], reverse=True)
    
    return {"job_id": job_id, "matches": matches[:20]}  # Top 20

# INTERVIEW ENDPOINTS

@router.post("/interviews/generate-questions")
async def generate_interview_questions(
    job_id: str,
    num_questions: int = 5,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Generate AI interview questions."""
    
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    questions = await question_generator.generate_questions(
        job.job_title,
        job.required_skills,
        job.experience_level,
        num_questions
    )
    
    return {
        "job_id": job_id,
        "questions": questions
    }

# RECRUITER COPILOT ENDPOINTS

@router.post("/copilot/analyze-candidate")
async def copilot_analyze_candidate(
    candidate_id: str,
    job_id: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """AI analysis of candidate-job fit."""
    
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.tenant_id == tenant_id
    ).first()
    
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id,
        JobDescription.tenant_id == tenant_id
    ).first()
    
    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or job not found")
    
    analysis = await recruiter_copilot.analyze_candidate(
        {
            "skills": candidate.skills,
            "summary": candidate.notes
        },
        {
            "job_title": job.job_title,
            "required_skills": job.required_skills,
            "experience_level": job.experience_level
        }
    )
    
    return analysis

# BILLING ENDPOINTS

@router.post("/billing/create-subscription")
async def create_subscription(
    plan: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Create subscription for tenant."""
    
    # Get customer ID from tenant
    tenant = db.query(Tenant).get(tenant_id)
    
    if not tenant or not tenant.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No customer on file")
    
    try:
        price_id = f"price_{plan}_usd"
        subscription = billing_service.create_subscription(
            tenant.stripe_customer_id,
            price_id
        )
        
        tenant.subscription_tier = plan
        tenant.stripe_subscription_id = subscription["subscription_id"]
        db.commit()
        
        return subscription
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/billing/usage")
async def get_usage(
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get current month usage."""
    usage = await usage_meter.get_month_usage(db, tenant_id)
    
    return {
        "tenant_id": tenant_id,
        "usage": usage,
        "period": "current_month"
    }

# Import Tenant model
from app.models.base import Tenant
