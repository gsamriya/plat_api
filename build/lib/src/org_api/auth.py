from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPAuthorizationCredentials, HTTPBearer

VALID_USERNAME = "admin"
VALID_PASSWORD = "secret"
VALID_TOKEN = "supersecrettoken"

# Define security schemes
basic_security = HTTPBasic(auto_error=False)
bearer_security = HTTPBearer(auto_error=False)


def verify_basic_auth(credentials: HTTPBasicCredentials) -> str:
    if not credentials or credentials.username != VALID_USERNAME or credentials.password != VALID_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect basic authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return VALID_USERNAME


def verify_token_auth(credentials: HTTPAuthorizationCredentials) -> str:
    if not credentials or credentials.scheme.lower() != "bearer" or credentials.credentials != VALID_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return VALID_USERNAME


# Unified authenticate dependency
async def authenticate(
        basic_credentials: HTTPBasicCredentials = Depends(basic_security),
        bearer_credentials: HTTPAuthorizationCredentials = Depends(bearer_security),
) -> str:
    if basic_credentials:
        try:
            return verify_basic_auth(basic_credentials)
        except HTTPException:
            pass
    if bearer_credentials:
        try:
            return verify_token_auth(bearer_credentials)
        except HTTPException:
            pass
    # If neither auth passed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": 'Basic, Bearer'},
    )
