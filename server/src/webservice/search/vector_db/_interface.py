from abc import ABC, abstractmethod

class VectorDB(ABC):
    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def retrieve(self, query_embedding, k):
        pass
