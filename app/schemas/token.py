from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    max_age: int

    class Config:
        orm_mode = True


class TokenData(BaseModel):
    user_id: int
