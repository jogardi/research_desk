from abc import ABC, abstractmethod

class VectorDB(ABC):
    @abstractmethod
    def _build_initial_index(self, embeddings, ids):
        pass

    @abstractmethod
    def add_items(self, embeddings, ids):
        pass
    
    @abstractmethod
    def item_count(self):
        pass
