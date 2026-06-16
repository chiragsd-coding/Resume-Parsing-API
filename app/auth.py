"""Authentication and authorization - JWT, OAuth, SAML."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthService:
    """JWT and OAuth authentication."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password for storage."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

class RBACService:
    """Role-Based Access Control."""
    
    ROLES = {
        "admin": ["*"],
        "recruiter": ["read", "write", "parse", "match", "interview"],
        "viewer": ["read"],
        "billing_admin": ["read", "billing"],
    }
    
    @staticmethod
    def has_permission(user_role: str, required_permission: str) -> bool:
        """Check if role has permission."""
        if user_role not in RBACService.ROLES:
            return False
        permissions = RBACService.ROLES[user_role]
        return "*" in permissions or required_permission in permissions
    
    @staticmethod
    def require_permission(required_permission: str):
        """Dependency for route protection."""
        async def check_permission(user: dict = Depends(get_current_user)):
            if not RBACService.has_permission(user.get("role"), required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return user
        return check_permission

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> dict:
    """Extract user from JWT token."""
    try:
        payload = AuthService.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if not user_id or not tenant_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id, "tenant_id": tenant_id, "role": payload.get("role", "recruiter")}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

async def get_current_tenant(user: dict = Depends(get_current_user)) -> str:
    """Extract tenant_id from current user."""
    return user.get("tenant_id")
