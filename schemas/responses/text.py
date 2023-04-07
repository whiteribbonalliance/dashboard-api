from pydantic import BaseModel, Field


class SubmitStatus(BaseModel):
    is_success: bool = Field(
        description='The status of the submission')
    error_message: str = Field(None, description='Description of the error message')
