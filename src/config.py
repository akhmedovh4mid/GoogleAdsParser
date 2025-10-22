from pathlib import Path

from pydantic import DirectoryPath, Field, FilePath, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    openai_api_key: str = Field(..., min_length=1)
    proxy_url: str | None = None


class PathSettings(BaseSettings):
    venv_path: Path = Path(".venv")
    main_script_path: FilePath = Path("main.py")
    requirements_path: FilePath = Path("requirements.txt")

    logs_dir: Path = Path("logs")
    log_file: Path = logs_dir / "google_parser.log"

    config_dir: DirectoryPath = Path("configs")
    prompt_file: FilePath = config_dir / "prompt.md"
    region_emails_file: FilePath = config_dir / "region_emails.json"
    device_schedule_file: FilePath = config_dir / "device_schedule.json"

    @field_validator("logs_dir", "config_dir")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Автоматическое создание директорий"""
        v.mkdir(exist_ok=True, parents=True)
        return v


class TimeoutSettings(BaseSettings):
    action_timeout: float = 0.5


class NumericalSettings(BaseSettings): ...


class Settings:
    env = EnvSettings()
    path = PathSettings()
    timeout = TimeoutSettings()
    numeric = NumericalSettings()


settings = Settings()
