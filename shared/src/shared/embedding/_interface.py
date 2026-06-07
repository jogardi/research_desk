from abc import ABC, abstractmethod

class EmbeddingModel(ABC):
    @abstractmethod
    def embed(self, text):
        pass

    @abstractmethod
    def embed_many(self, texts):
        pass

    @abstractmethod
    def dim(self):
        pass

