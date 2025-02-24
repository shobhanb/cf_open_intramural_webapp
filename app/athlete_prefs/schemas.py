import datetime as dt

from app.schemas import CustomBaseModel


class AthletePrefsModel(CustomBaseModel):
    name: str
    team_name: str
    mf_age_category: str
    rx_pref: str
    preference_nbr: int
    preference: str
    updated_at: dt.datetime
    created_at: dt.datetime
