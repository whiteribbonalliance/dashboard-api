from pydantic import BaseModel, Field


class DateFilter(BaseModel):
    from_date: str | None = Field(description="From date")
    to_date: str | None = Field(description="To date")
