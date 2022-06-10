import requests

from .models import DalleResponse
from .exceptions import DalleTemporarilyUnavailableException
from ...settings import Settings

__all__ = ("Dalle",)


class Dalle:
    def __init__(self, settings: Settings):
        self._settings = settings

    def generate(self, prompt: str) -> DalleResponse:
        return self._simple_request(prompt)

    def _simple_request(self, prompt: str) -> DalleResponse:
        body = dict(
            prompt=prompt
        )
        response = requests.post(
            url=self._settings.dalle_api_url,
            json=body,
            timeout=1000  # TODO parametrize in settings
        )

        return self._parse_response(
            response=response,
            prompt=prompt,
        )

    @staticmethod
    def _parse_response(prompt: str, response: requests.Response) -> DalleResponse:
        if response.status_code != 200:
            if response.status_code == 503:
                raise DalleTemporarilyUnavailableException()
            response.raise_for_status()

        return DalleResponse(
            **response.json(),
            prompt=prompt,
        )
