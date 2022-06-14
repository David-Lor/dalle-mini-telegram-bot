import abc


class AbstractLogger(abc.ABC):
    @abc.abstractmethod
    def log(self, data: str):
        """
        :param data: log record as JSON string
        """
        pass
