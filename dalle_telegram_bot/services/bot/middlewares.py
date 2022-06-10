import contextlib

from ...logger import logger
from ...utils import get_uuid


@contextlib.contextmanager
def request_middleware():
    request_id = get_uuid()
    with logger.contextualize(request_id=request_id):
        try:
            logger.info("Request started")
            yield
        except Exception as ex:
            logger.exception("Request failed", ex)
        else:
            logger.info("Request completed")
