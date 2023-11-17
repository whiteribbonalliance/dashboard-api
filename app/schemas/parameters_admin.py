from pydantic import BaseModel


class ParametersAdmin(BaseModel):
    username: str
