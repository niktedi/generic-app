"""Application configuration from environment variables.

A single typed settings object is the one place DB and runtime values are
read. In Kubernetes (Phase 4) these come from a ConfigMap + Secret; locally
they come from the .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "calendar"
    db_user: str = "postgres"
    db_password: str = ""

    app_version: str = "dev"
    pod_name: str = "local"
    node_name: str = "local"


settings = Settings()
