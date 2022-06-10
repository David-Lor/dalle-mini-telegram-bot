import pydantic


class Settings(pydantic.BaseSettings):
    telegram_bot_token: str
    command_generate_action: str = "typing"

    class Config:
        env_file = ".env"
