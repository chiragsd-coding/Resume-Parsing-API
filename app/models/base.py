"""SQLAlchemy ORM models for multi-tenant ATS platform."""
from datetime import datetime, timedelta
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, ForeignKey, 
    Text, JSON, Enum, UniqueConstraint, Index, LargeBinary
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
import uuid

Base = declarative_base()

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"

# MULTI-TENANT CORE MODELS

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    logo_url = Column(String(500))
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    
    # Billing
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    monthly_resume_limit = Column(Integer, default=50)
    resumes_used_this_month = Column(Integer, default=0)
    reset_date = Column(DateTime, default=datetime.utcnow)
    
    # Features
    features = Column(JSON, default={})  # Feature flags
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    api_keys = relationship("ApiKey", back_populates="tenant")
    resumes = relationship("Resume", back_populates="tenant")
    job_descriptions = relationship("JobDescription", back_populates="tenant")
    candidates = relationship("Candidate", back_populates="tenant")
    
    __table_args__ = (Index("idx_tenant_slug", "slug"),)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255))
    full_name = Column(String(255))
    role = Column(String(50), default="recruiter")  # admin, recruiter, viewer
    
    # OAuth
    oauth_provider = Column(String(50))  # google, saml, oauth
    oauth_id = Column(String(255))
    
    # RBAC
    permissions = Column(JSON, default={})
    
    # Status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    api_keys = relationship("ApiKey", back_populates="user")
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_email"),
        Index("idx_user_email", "email"),
    )

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    name = Column(String(255))
    key_hash = Column(String(255), nullable=False, unique=True)
    
    # Permissions
    scopes = Column(JSON, default=["read", "write"])  # Fine-grained permissions
    
    # Rate limit
    rate_limit_calls = Column(Integer, default=100)
    rate_limit_period = Column(Integer, default=60)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=365))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
    user = relationship("User", back_populates="api_keys")

# RESUME & JOB DESCRIPTION MODELS

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id"))
    
    # File
    file_name = Column(String(255))
    file_path = Column(String(500))
    file_hash = Column(String(255), unique=True)  # For duplicate detection
    
    # Parsed Data
    raw_text = Column(Text)
    parsed_data = Column(JSON)
    
    # Embeddings & Search
    embedding = Column(LargeBinary)  # Vector embedding
    
    # Extracted Info
    full_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(20))
    location = Column(String(255))
    summary = Column(Text)
    skills = Column(JSON, default=[])
    experience = Column(JSON, default=[])
    education = Column(JSON, default=[])
    certifications = Column(JSON, default=[])
    
    # Processing
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    parsing_job_id = Column(String(255))
    error_message = Column(Text)
    
    # Metadata
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(String(36), ForeignKey("resumes.id"))
    confidence_score = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="resumes")
    candidate = relationship("Candidate", back_populates="resumes")
    
    __table_args__ = (
        Index("idx_resume_tenant_status", "tenant_id", "status"),
        Index("idx_resume_candidate", "candidate_id"),
    )

class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Basic Info
    full_name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    location = Column(String(255))
    
    # Aggregated Data
    skills = Column(JSON, default=[])
    total_experience_years = Column(Float)
    highest_education_level = Column(String(100))
    
    # Status
    status = Column(String(50), default="new")  # new, reviewing, rejected, hired
    rating = Column(Float)  # 1-5
    notes = Column(Text)
    
    # Deduplication
    is_duplicate = Column(Boolean, default=False)
    merged_with_id = Column(String(36), ForeignKey("candidates.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="candidates")
    resumes = relationship("Resume", back_populates="candidate")
    matches = relationship("CandidateMatch", foreign_keys="CandidateMatch.candidate_id", back_populates="candidate")
    
    __table_args__ = (
        Index("idx_candidate_tenant_email", "tenant_id", "email"),
    )

class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Basic Info
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255))
    job_description = Column(Text)
    
    # Parsed Data
    parsed_data = Column(JSON)
    
    # Extracted Info
    required_skills = Column(JSON, default=[])
    nice_to_have_skills = Column(JSON, default=[])
    experience_level = Column(String(100))  # junior, mid, senior, lead
    years_experience_required = Column(Float)
    location = Column(String(255))
    salary_min = Column(Float)
    salary_max = Column(Float)
    
    # Embeddings
    embedding = Column(LargeBinary)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="job_descriptions")
    matches = relationship("CandidateMatch", back_populates="job_description")
    
    __table_args__ = (
        Index("idx_jd_tenant_active", "tenant_id", "is_active"),
    )

# MATCHING & ANALYSIS MODELS

class CandidateMatch(Base):
    __tablename__ = "candidate_matches"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id"), nullable=False, index=True)
    job_description_id = Column(String(36), ForeignKey("job_descriptions.id"), nullable=False, index=True)
    
    # Match Scores
    overall_score = Column(Float)  # 0-100
    skill_match_score = Column(Float)
    experience_match_score = Column(Float)
    education_match_score = Column(Float)
    
    # Details
    matching_skills = Column(JSON, default=[])
    missing_skills = Column(JSON, default=[])
    skill_gap_analysis = Column(JSON)
    
    # Status
    status = Column(String(50), default="active")  # active, rejected, interviewed, hired
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="matches")
    job_description = relationship("JobDescription", back_populates="matches")
    
    __table_args__ = (
        Index("idx_match_overall_score", "overall_score"),
        Index("idx_match_job_score", "job_description_id", "overall_score"),
    )

class SkillGapAnalysis(Base):
    __tablename__ = "skill_gap_analysis"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id"))
    job_description_id = Column(String(36), ForeignKey("job_descriptions.id"))
    
    # Gap Analysis
    gaps = Column(JSON)  # Required but missing skills
    surplus = Column(JSON)  # Extra skills candidate has
    recommendations = Column(JSON)  # Learning recommendations
    
    created_at = Column(DateTime, default=datetime.utcnow)

# INTERVIEW & COPILOT MODELS

class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id"))
    job_description_id = Column(String(36), ForeignKey("job_descriptions.id"))
    
    # Config
    num_questions = Column(Integer, default=5)
    focus_areas = Column(JSON)  # Technical, behavioral, etc.
    
    # Questions
    questions = Column(JSON, default=[])
    
    # Status
    status = Column(String(50), default="draft")  # draft, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class InterviewAnswer(Base):
    __tablename__ = "interview_answers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("interview_sessions.id"))
    question_index = Column(Integer)
    
    candidate_answer = Column(Text)
    ai_evaluation = Column(JSON)  # Score, feedback, sentiment
    ai_followup = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# AUDIT & COMPLIANCE MODELS

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    
    action = Column(Enum(AuditAction))
    resource_type = Column(String(50))  # resume, candidate, job, etc.
    resource_id = Column(String(36))
    
    changes = Column(JSON)  # What changed
    ip_address = Column(String(45))
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("idx_audit_tenant_date", "tenant_id", "created_at"),
    )

class BillingEvent(Base):
    __tablename__ = "billing_events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True)
    
    event_type = Column(String(50))  # resume_processed, api_call, etc.
    quantity = Column(Float)
    cost = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class UsageMetric(Base):
    __tablename__ = "usage_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True)
    
    metric_name = Column(String(255))
    value = Column(Float)
    period = Column(String(20))  # hourly, daily, monthly
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("idx_usage_tenant_metric", "tenant_id", "metric_name"),
    )
