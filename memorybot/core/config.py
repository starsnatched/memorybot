from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DISCORD_",
        case_sensitive=False,
        extra="ignore",
    )

    token: str
    application_id: int | None = None
    owner_ids: List[int] = Field(default_factory=list)
    owner_id: int | None = None
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: str | None = None
    log_datefmt: str | None = None

    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, validation_alias="OPENAI_BASE_URL")
    openai_api_base: Optional[str] = Field(default=None, validation_alias="OPENAI_API_BASE")
    openai_model: str = Field(default="gpt-4o-2024-08-06", validation_alias="OPENAI_MODEL")

    database_url: str = Field(default="sqlite+aiosqlite:///./memorybot.db", validation_alias="DATABASE_URL")

    @field_validator("owner_ids", mode="before")
    @classmethod
    def parse_csv_ints(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return [int(x) for x in v]
        return [int(x.strip()) for x in str(v).split(",") if x.strip()]

    def model_post_init(self, __context):
        if self.owner_id and self.owner_id not in self.owner_ids:
            self.owner_ids.append(self.owner_id)


class RuntimeConfig(BaseModel):
    settings: Settings


def load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        import sys
        errs = e.errors()
        missing = [".".join(str(x) for x in err.get("loc", [])) for err in errs if err.get("type") == "missing"]
        if missing:
            sys.stderr.write(
                "Configuration missing: " + ", ".join(missing) + 
                ". Set DISCORD_* environment variables or use a .env file.\n"
            )
        else:
            details = "; ".join(
                f"{'.'.join(str(x) for x in err.get('loc', []))}: {err.get('msg')}" for err in errs
            )
            sys.stderr.write("Invalid configuration: " + details + "\n")
        raise SystemExit(2)
