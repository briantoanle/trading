from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application settings and API keys loaded from environment variables.

    Attributes:
        nvidia_api_key (str): The API key for the NVIDIA NIM service. Defaults to "NVCF-DEFAULT".
        nvidia_api_base (str): The base URL for the NVIDIA NIM API.
    """
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    nvidia_api_key: str = "NVCF-DEFAULT"
    nvidia_api_base: str = "https://integrate.api.nvidia.com/v1"

# Instantiate a single settings object to be used throughout the application
settings = Settings()
