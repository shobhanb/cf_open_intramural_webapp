from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    url: str = "sqlite+aiosqlite:///test.db"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="db_", extra="ignore")


db_settings = DBSettings()
