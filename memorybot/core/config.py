from typing import List, Literal
from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DISCORD_", case_sensitive=False)

    token: str
    application_id: int | None = None
    owner_ids: List[int] = Field(default_factory=list)
    owner_id: int | None = None
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

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
        raise SystemExit(2) from e
