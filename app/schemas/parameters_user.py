from pydantic import BaseModel


class ParametersUser(BaseModel):
    username: str
