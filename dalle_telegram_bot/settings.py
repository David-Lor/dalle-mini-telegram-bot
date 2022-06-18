from typing import Optional

import pydantic


class Settings(pydantic.BaseSettings):
    telegram_bot_token: str
    telegram_bot_threads: int = 500
    telegram_bot_delete_webhook: bool = False
    telegram_bot_graceful_shutdown: bool = False
    telegram_bot_set_commands: bool = False
    telegram_bot_api_sessions_enabled: bool = True
    telegram_bot_api_sessions_ttl_seconds: float = 360
    telegram_bot_ratelimit_retry: bool = True
    telegram_bot_ratelimit_retry_delay_seconds: float = 5
    telegram_bot_ratelimit_retry_timeout_seconds: float = 120

    command_generate_action: str = "typing"
    command_generate_chat_concurrent_limit: int = 3
    command_generate_prompt_length_min: int = pydantic.Field(default=2, gt=1)
    command_generate_prompt_length_max: int = pydantic.Field(default=1000, gt=1)

    dalle_api_url: pydantic.AnyHttpUrl = "https://bf.dallemini.ai/generate"
    dalle_api_request_timeout_seconds: float = 3.5 * 60
    dalle_api_request_socks_proxy: Optional[pydantic.AnyUrl] = None
    dalle_generation_timeout_seconds: float = 6 * 60
    dalle_generation_retry_delay_seconds: float = 5

    redis_host: Optional[str] = None
    redis_port: int = 6379
    redis_db: int = 0
    redis_username: Optional[str] = None
    redis_password: Optional[str] = None
    redis_logs_queue_name: Optional[str] = None

    log_level: str = "INFO"

    @property
    def dalle_generation_retries_limit(self) -> int:
        return int(self.dalle_generation_timeout_seconds / self.dalle_generation_retry_delay_seconds)

    @property
    def telegram_bot_ratelimit_retries_limit(self) -> int:
        return int(self.telegram_bot_ratelimit_retry_timeout_seconds / self.telegram_bot_ratelimit_retry_delay_seconds)

    @property
    def dalle_api_request_socks_proxy_for_requests_lib(self) -> Optional[dict]:
        if not self.dalle_api_request_socks_proxy:
            return None
        proxy = str(self.dalle_api_request_socks_proxy)
        return dict(
            http=proxy,
            https=proxy,
        )

    class Config:
        env_file = ".env"
