import pydantic


class Settings(pydantic.BaseSettings):
    telegram_bot_token: str
    command_generate_action: str = "typing"
    dalle_api_url: pydantic.AnyHttpUrl = "https://bf.dallemini.ai/generate"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
