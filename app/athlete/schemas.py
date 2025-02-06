from app.schemas import CustomBaseModel


class AthleteBaseModel(CustomBaseModel):
    year: int
    affiliate_id: int
    competitor_id: int
    name: str
    gender: str
    mf_age_category: str
