__all__ = ("BaseDalleException", "DalleTemporarilyUnavailableException")


class BaseDalleException(Exception):
    pass


class DalleTemporarilyUnavailableException(BaseDalleException):
    pass
