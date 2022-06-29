from abc import ABC, abstractmethod


class StaircaseLogger(ABC):
    @abstractmethod
    def info(self, *args, **kwargs):
        pass

    @abstractmethod
    def error(self, *args, **kwargs):
        pass


class DefaultLogger(StaircaseLogger):
    def info(self, *args, **kwargs):
        print(*args, **kwargs)

    def error(self, *args, **kwargs):
        print(*args, **kwargs)

    @staticmethod
    def get_default() -> 'StaircaseLogger':
        return DefaultLogger()
