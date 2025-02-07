from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    url: str = "sqlite+aiosqlite:///test.db"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="db_", extra="ignore")


class AuthSettings(BaseSettings):
    admin_username: str = "admin"
    admin_password: str = "password"  # noqa: S105
    secret_key: str = "secretkey"  # noqa: S105
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10
    refresh_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_prefix="auth_", extra="ignore")


db_settings = DBSettings()
auth_settings = AuthSettings()
