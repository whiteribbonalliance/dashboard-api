"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

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


class InternalServerErrorHTTPException(HTTPException):
    def __init__(self, detail: str = None):
        if not detail:
            detail = "Internal server error"
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )
