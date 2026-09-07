from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

class Settings(BaseSettings):
    DATABASE_URL: str
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"  

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

            # asyncpg does not accept 'sslmode' or 'channel_binding', it expects 'ssl'
            parsed = urlparse(v)
            if parsed.query:
                query_params = parse_qsl(parsed.query)
                new_params = []
                for k, val in query_params:
                    if k == "sslmode":
                        if val in ("require", "verify-ca", "verify-full", "prefer"):
                            new_params.append(("ssl", "require"))
                    elif k in ("channel_binding",):
                        continue
                    else:
                        new_params.append((k, val))
                v = urlunparse(parsed._replace(query=urlencode(new_params)))
        return v

    model_config = SettingsConfigDict(
        env_file="backend/.env",
        extra='ignore'
    )

config = Settings()

