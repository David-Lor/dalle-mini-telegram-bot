import abc


class Setupable(abc.ABC):

    @abc.abstractmethod
    def setup(self):
        pass

    @abc.abstractmethod
    def teardown(self):
        pass
