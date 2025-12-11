import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import make_url

# Default for local OR Railway (both work)
DEFAULT_DB_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/keyrythm"
#DEFAULT_DB_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/keyrythm"
class Settings(BaseSettings):
    app_name: str = "TypeShield Authenticator"
    secret_key: str = Field("super-secret-key-change-me", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    database_url: str = Field(
        DEFAULT_DB_URL,
        env="DATABASE_URL",
    )

    behaviour_threshold: float = Field(75.0, env="BEHAVIOUR_THRESHOLD")
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # FIX: normalize the DB URL for SQLAlchemy
    def normalized_db_url(self) -> str:
        url = make_url(self.database_url)

        # Railway may give "postgresql://"
        if url.drivername == "postgresql":
            url = url.set(drivername="postgresql+psycopg2")

        # In case someone uses postgres://
        if url.drivername == "postgres":
            url = url.set(drivername="postgresql+psycopg2")

        return str(url)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
