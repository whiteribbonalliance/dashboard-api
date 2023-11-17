from pydantic import BaseModel, Field


class DataIsLoading(BaseModel):
    is_loading: bool = Field(description="Is data reloading.")
