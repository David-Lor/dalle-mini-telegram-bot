import requests
import wait4it

from .models import DalleResponse
from .exceptions import DalleTemporarilyUnavailableException
from ...settings import Settings
from ...logger import logger

__all__ = ("Dalle",)


class Dalle:
    def __init__(self, settings: Settings):
        self._settings = settings

        self._generate_until_complete = wait4it.wait_for_pass(
            exceptions=(DalleTemporarilyUnavailableException,),
            retries=self._settings.dalle_generation_retries_limit,
            retries_delay=self._settings.dalle_generation_retry_delay_seconds,
        )(lambda prompt: self._simple_request(prompt))

    def generate(self, prompt: str) -> DalleResponse:
        return self._generate_until_complete(prompt)

    def _simple_request(self, prompt: str) -> DalleResponse:
        logger.debug("Requesting DALLE...")
        body = dict(
            prompt=prompt,
        )
        response = requests.post(
            url=self._settings.dalle_api_url,
            json=body,
            timeout=self._settings.dalle_api_request_timeout_seconds,
            proxies=self._settings.dalle_api_request_socks_proxy_for_requests_lib,
        )
        logger.bind(status_code=response.status_code).debug("DALLE response received")

        return self._parse_response(
            response=response,
            prompt=prompt,
        )

    @staticmethod
    def _parse_response(prompt: str, response: requests.Response) -> DalleResponse:
        if response.status_code == 503:
            raise DalleTemporarilyUnavailableException()
        response.raise_for_status()

        return DalleResponse(
            **response.json(),
            prompt=prompt,
        )
