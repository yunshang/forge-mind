from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://token-plan-cn.xiaomimimo.com/anthropic"
    anthropic_model: str = "mimo-v2.5-pro"
    anvil_url: str = "http://localhost:8545"
    anvil_chain_id: int = 31337
    solc_path: str = "solc"
    max_healing_iterations: int = 3
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_prefix": "FORGE_", "env_file": str(_ENV_FILE)}


settings = Settings()
