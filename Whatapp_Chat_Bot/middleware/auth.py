"""Authentication middleware"""
from typing import Optional, Callable
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.authentication import AuthenticationBackend, AuthCredentials, SimpleUser
from jose import jwt, JWTError
from config.settings import get_settings

settings = get_settings()

class JWTAuthBackend(AuthenticationBackend):
    """JWT authentication backend"""
    
    async def authenticate(self, request: Request):
        if "Authorization" not in request.headers:
            return None
            
        auth = request.headers["Authorization"]
        try:
            scheme, token = auth.split()
            if scheme.lower() != "bearer":
                return None
                
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            return AuthCredentials(["authenticated"]), SimpleUser(payload.get("sub"))
            
        except (ValueError, JWTError) as e:
            return None

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication"""
    
    def __init__(self, app):
        super().__init__(app)
        self.public_paths = {"/health", "/metrics", "/docs", "/openapi.json"}
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> None:
        """Process each request for authentication"""
        # Skip auth for public endpoints
        if request.url.path in self.public_paths:
            return await call_next(request)
            
        # Get and validate token
        auth = request.headers.get("Authorization")
        if not auth:
            raise HTTPException(
                status_code=401,
                detail="Missing authentication token"
            )
            
        try:
            scheme, token = auth.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication scheme"
                )
                
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Add user info to request state
            request.state.user = payload.get("sub")
            request.state.user_id = payload.get("user_id")
            
            return await call_next(request)
            
        except (ValueError, JWTError) as e:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
