import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        self.BRIGHT_DATA_API_KEY: str = os.getenv("BRIGHT_DATA_API_KEY", "")
        self.DATABASE_PATH: str = os.getenv("DATABASE_PATH", os.path.join(os.getcwd(), "data", "sentinel_chain.db"))
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.HOST: str = os.getenv("HOST", "127.0.0.1")
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        self.DEFAULT_COLLECTOR_ID: str = os.getenv("DEFAULT_COLLECTOR_ID", "c_sentinel_cve_threats")
        self.TARGET_DEMO_URL: str = os.getenv("TARGET_DEMO_URL", f"http://127.0.0.1:{self.PORT}/api/proxy/target")
        self.CLI_TIMEOUT_SECONDS: int = int(os.getenv("CLI_TIMEOUT_SECONDS", "120"))
        self.HEAL_TIMEOUT_SECONDS: int = int(os.getenv("HEAL_TIMEOUT_SECONDS", "180"))

@lru_cache()
def get_settings() -> Settings:
    return Settings()
