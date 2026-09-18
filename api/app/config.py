from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Only these hosts may ever be contacted from the API container (docs/DATA_SOURCES.md).
OUTBOUND_ALLOWLIST: tuple[str, ...] = (
    "www.cisa.gov",
    "epss.cyentia.com",
    "api.first.org",
    "api.osv.dev",
    "services.nvd.nist.gov",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://frist24:frist24@localhost:5432/frist24"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_fallback_model: str = "mistral"

    frist24_manufacturer_name: str = "Beispiel Maschinenbau GmbH"
    frist24_manufacturer_contact: str = "psirt@beispiel-maschinenbau.example"

    kev_url: str = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    epss_csv_url: str = "https://epss.cyentia.com/epss_scores-current.csv.gz"
    osv_api_url: str = "https://api.osv.dev/v1"
    sync_interval_minutes: int = 15

    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
