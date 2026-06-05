import logging
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status
from app.services.auth import create_access_token

router = APIRouter()
logger = logging.getLogger("askdocs-rag.api.auth")

class TokenRequest(BaseModel):
    username: str = Field(..., description="Username for token generation", example="sreeram")
    role: str = Field(..., description="User role (admin, engineering, hr, public)", example="engineering")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT Bearer token")
    token_type: str = Field(default="bearer", description="Token schema type")

@router.post("/auth/token", response_model=TokenResponse, status_code=status.HTTP_200_OK, tags=["auth"])
async def login_for_access_token(request: TokenRequest):
    """
    Generates a JWT Token for testing local RAG RBAC policies.
    Accepts roles: admin, engineering, hr, public.
    """
    role = request.role.lower().strip()
    if role not in ("admin", "engineering", "hr", "public"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be one of: admin, engineering, hr, public"
        )
        
    logger.info(f"Generating JWT access token for '{request.username}' with role '{role}'")
    
    # Generate JWT token with sub and role claims
    access_token = create_access_token(
        data={"sub": request.username, "role": role}
    )
    
    return TokenResponse(access_token=access_token)
