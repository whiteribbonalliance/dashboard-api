"""HTTP Exceptions"""

from fastapi import status, HTTPException


class ResourceNotFoundHTTPException(HTTPException):
    def __init__(self, detail: str = None):
        if not detail:
            detail = "Resource not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class FailedCreatingResourceHTTPException(HTTPException):
    def __init__(self, detail: str = None):
        if not detail:
            detail = "Failed when creating resource"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ConflictHTTPException(HTTPException):
    def __init__(self, detail: str = None):
        if not detail:
            detail = "Conflict"
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ForbiddenHTTPException(HTTPException):
    def __init__(self, detail: str = None):
        if not detail:
            detail = "Forbidden"
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthorizedHTTPException(HTTPException):
    def __init__(self, detail: str = None):
        if not detail:
            detail = "Unauthorized"
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class LimitExceededHTTPException(HTTPException):
    def __init__(self, detail: str = None):
        if not detail:
            detail = "Too many requests, try again later"
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class NotAllowedHTTPException(HTTPException):
    def __init__(self, detail: str = None):
        if not detail:
            detail = "Not allowed"
        super().__init__(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=detail)
