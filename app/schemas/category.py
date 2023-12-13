from pydantic import BaseModel


class SubCategory(BaseModel):
    code: str
    description: str


class ParentCategory(BaseModel):
    code: str
    description: str
    sub_categories: list[SubCategory]
