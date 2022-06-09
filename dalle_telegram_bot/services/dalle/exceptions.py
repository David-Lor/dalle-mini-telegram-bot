__all__ = ("BaseDalleException", "DalleTemporarilyUnavailableException", "DalleUnknownError")


class BaseDalleException(Exception):
    pass


class DalleTemporarilyUnavailableException(BaseDalleException):
    pass


class DalleUnknownError(BaseDalleException):
    pass
