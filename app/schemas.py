from pydantic import BaseModel


class CustomBaseModel(BaseModel):
    class Config:
        from_attributes = True
        populate_by_name = True
