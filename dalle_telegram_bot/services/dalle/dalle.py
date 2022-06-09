import requests

from .models import DalleResponse
from .exceptions import DalleTemporarilyUnavailableException
from ...settings import Settings

URL = "https://bf.dallemini.ai/generate"


class Dalle:
    def __init__(self, settings: Settings):
        self._settings = settings

    def _simple_request(self, text: str):
        body = dict(
            prompt=text
        )
        response = requests.post(
            url=URL,
            json=body,
            timeout=1000  # TODO parametrize in settings
        )

        return self._parse_response(
            response=response,
            prompt=text,
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
