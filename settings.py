from pydantic import BaseSettings, Json, PostgresDsn, AnyHttpUrl
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings"""

    DB_DSN: PostgresDsn
    TIMETABLE_NAME: str

    class Config:
        """Pydantic BaseSettings config"""

        case_sensitive = True
        env_file = "../.env"
