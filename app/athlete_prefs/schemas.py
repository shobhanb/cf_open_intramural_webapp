from app.schemas import CustomBaseModel


class AthletePrefsModel(CustomBaseModel):
    name: str
    rx_pref: str
    preference_nbr: int
    preference: str
