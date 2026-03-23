from fastapi import HTTPException
from pydantic import BaseModel
import logging

class APIError(Exception):
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(APIError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=400, details=details)

class AuthorizationError(APIError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=401, details=details)

class NotFoundError(APIError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=404, details=details)

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    return logger
