from typing import Optional

import pydantic


class Settings(pydantic.BaseSettings):
    telegram_bot_token: str
    telegram_bot_threads: int = 500

    command_generate_action: str = "typing"
    command_generate_chat_concurrent_limit: int = 3

    dalle_api_url: pydantic.AnyHttpUrl = "https://bf.dallemini.ai/generate"
    dalle_api_request_timeout_seconds: float = 3.5 * 60
    dalle_api_request_socks_proxy: Optional[pydantic.AnyUrl] = None
    dalle_generation_timeout_seconds: float = 6 * 60
    dalle_generation_retry_delay_seconds: float = 5

    log_level: str = "INFO"

    @property
    def dalle_generation_retries_limit(self) -> int:
        return int(self.dalle_generation_timeout_seconds / self.dalle_generation_retry_delay_seconds)

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
