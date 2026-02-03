"""JWT authentication for incoming webhook requests."""

import jwt
import logging
from datetime import datetime, timezone
from typing import Callable
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

_LOGGER = logging.getLogger(__name__)
security = HTTPBearer()


def verify_jwt_token(token: str, jwt_secret: str) -> dict:
    """
    Verify JWT token and return the payload.
    
    Args:
        token: JWT token string to verify
        jwt_secret: Secret key for token verification
        
    Returns:
        Decoded token payload as dict

        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"]
        )
        
        # Check expiration time if present
        if "exp" in payload:
            exp_timestamp = payload["exp"]
            if datetime.now(timezone.utc).timestamp() > exp_timestamp:
                _LOGGER.warning("JWT token expired")
                raise HTTPException(
                    status_code=401,
                    detail="Token expired"
                )
        
        _LOGGER.debug(
            "JWT token verified successfully for issuer: %s",
            payload.get("iss", "unknown")
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        _LOGGER.warning("JWT token expired")
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )
    except jwt.InvalidTokenError as e:
        _LOGGER.warning("Invalid JWT token: %s", e)
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    except Exception as e:
        _LOGGER.error("Unexpected error during JWT verification: %s", e)
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )


def create_auth_dependency(jwt_secret: str) -> Callable:
    """
    Create a FastAPI dependency for JWT authentication.
    
    This factory function returns a configured authentication dependency
    that can be used in FastAPI endpoint definitions.
    
    Args:
        jwt_secret: Secret key for JWT token verification
        
    Returns:
        Async dependency function ready to use with Depends()
    """
    async def verify_authentication(
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> dict:
        """
        FastAPI dependency that verifies JWT authentication.
        
        Args:
            credentials: HTTP authorization credentials from request header
            
        Returns:
            Decoded JWT payload
        """
        token = credentials.credentials
        return verify_jwt_token(token, jwt_secret)
    
    return verify_authentication

