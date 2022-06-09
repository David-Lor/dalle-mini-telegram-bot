import pydantic


class Settings(pydantic.BaseSettings):
    telegram_bot_token: str

    class Config:
        env_file = ".env"
