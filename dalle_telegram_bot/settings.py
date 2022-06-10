import pydantic


class Settings(pydantic.BaseSettings):
    telegram_bot_token: str
    command_generate_action: str = "typing"
    command_generate_chat_concurrent_limit: int = 3
    dalle_api_url: pydantic.AnyHttpUrl = "https://bf.dallemini.ai/generate"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
