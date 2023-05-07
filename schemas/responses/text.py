from pydantic import BaseModel, Field


class FilterResponse(BaseModel):
    todo_data_for_the_graphs_and_excerpt: bool = Field(
        description='Needs to be populated')
    error_message: str = Field(None, description='Description of the error message')
