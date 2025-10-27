from typing import Dict, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from jose import jwt
import requests
import base64
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from utils.logger import get_logger

logger = get_logger("auth_middleware")

JWKS_CACHE = {}

# Function to convert JWK to PEM format
def jwk_to_pem(jwk: Dict) -> str:
    try:
        modulus = base64.urlsafe_b64decode(jwk['n']+'==')
        exponent = base64.urlsafe_b64decode(jwk['e']+'==')
        
        modulus_int = int.from_bytes(modulus, byteorder='big')
        exponent_int = int.from_bytes(exponent, byteorder='big')

        public_key = rsa.RSAPublicNumbers(exponent_int, modulus_int).public_key(default_backend())
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    except Exception as e:
        logger.error("Failed to convert JWK to PEM", error=str(e))
        raise

# Function to fetch the public keys
def get_cognito_public_keys(user_pool_id: str, aws_region: str) -> Optional[Dict]:
    if user_pool_id in JWKS_CACHE:
        logger.debug("Using cached JWKS", user_pool_id=user_pool_id)
        return JWKS_CACHE[user_pool_id]  

    jwks_url = f"https://cognito-idp.{aws_region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    logger.info("Fetching JWKS from Cognito", url=jwks_url)

    try:
        response = requests.get(jwks_url)
        response.raise_for_status()
        JWKS_CACHE[user_pool_id] = {key["kid"]: jwk_to_pem(key) for key in response.json()["keys"]}
        logger.info("JWKS fetched and cached successfully", key_count=len(JWKS_CACHE[user_pool_id]))
        return JWKS_CACHE[user_pool_id]
    except requests.RequestException as e:
        logger.error("Failed to fetch JWKS from Cognito", error=str(e), url=jwks_url)
        return None

# Middleware for authentication
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Skip root path (or any other exempted paths)
        if request.url.path == '/':
            return await call_next(request)
        
        logger.info("Processing authentication request", path=request.url.path)
        
        auth_headers = request.headers.get('Authorization')

        if not auth_headers or not auth_headers.startswith("Bearer "):
            logger.warning("Missing or invalid authorization header")
            raise HTTPException(status_code=401, detail="Missing or Invalid Token")
        
        # Extract token from Bearer header
        token = auth_headers.split("Bearer ")[1]

        # Extract the user pool, region, and app client ID from the request headers
        userpool_id = request.headers.get('userpool_id')
        aws_region = request.headers.get('aws_region')
        app_client_id = request.headers.get('client_id')

        if not userpool_id or not aws_region or not app_client_id:
            logger.warning(
                "Missing required headers for authentication",
                has_userpool_id=bool(userpool_id),
                has_aws_region=bool(aws_region),
                has_client_id=bool(app_client_id)
            )
            raise HTTPException(status_code=401, detail="Userpool or AWS region or client ID are missing")
        
        try:
            # Decode JWT header to get the 'kid' (key ID)
            header = jwt.get_unverified_header(token)
            if not header or 'kid' not in header:
                logger.error("Invalid token header - missing 'kid'")
                raise HTTPException(status_code=401, detail="Invalid token header: Missing 'kid'")

            jwks_keys = get_cognito_public_keys(userpool_id, aws_region)

            if not jwks_keys or header["kid"] not in jwks_keys:
                logger.error("Invalid token header - key not found", kid=header.get("kid"))
                raise HTTPException(status_code=401, detail="Invalid token header: Key not found")

            # Get the public key in PEM format
            public_key = jwks_keys[header["kid"]]

            # Decode the JWT and verify it with the public key, audience, and issuer
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=app_client_id,
                issuer=f"https://cognito-idp.{aws_region}.amazonaws.com/{userpool_id}"
            )
            
            duration = time.time() - start_time
            logger.info(
                "Authentication successful",
                duration=duration,
                user_id=payload.get("sub"),
                username=payload.get("cognito:username")
            )
            
            # Store the decoded payload in the request state
            request.state.user = payload
            return await call_next(request)

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Authentication failed",
                duration=duration,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
