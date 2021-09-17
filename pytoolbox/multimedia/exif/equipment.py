import abc, re

__all__ = ['Equipement']


class Equipement(object, metaclass=abc.ABCMeta):

    def __init__(self, metadata):
        self.metadata = metadata

    def __bool__(self):
        return bool(self.model)

    def __eq__(self, other):
        try:
            return self.brand == other.brand and self.model == other.model
        except AttributeError:
            return NotImplemented

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.brand} {self.model}>'

    @property
    @abc.abstractmethod
    def brand(self):
        pass

    @property
    def model(self):
        if self.brand and self._model:
            return re.sub(fr'{self.brand}\s+', '', self._model, 1, re.IGNORECASE)
        return self._model

    @property
    @abc.abstractmethod
    def _model(self):
        pass

    @property
    @abc.abstractmethod
    def tags(self):
        pass

    def refresh(self):
        self.__dict__.pop('tags', None)
