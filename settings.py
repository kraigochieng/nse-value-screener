from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_api_key: str
    gemini_api_key: str

    model_config = SettingsConfigDict(env_file=find_dotenv())


settings = Settings()
