import annoy
from vector_db._interface import VectorDB
import os

class AnnoyVectorDB(VectorDB):
    def __init__(self, db_file_path: str, dim: int, n_trees=10, metric='angular'):
        """Initialize the database instance with the given database file path."""
        self.index = annoy.AnnoyIndex(dim, metric)
        self.db_file_path = db_file_path
        self.n_trees = n_trees

    def _build_initial_index(self, embeddings, ids):
        """Build the initial index with the provided embeddings and ids."""
        for embedding, id in zip(embeddings, ids):
            self.index.add_item(id, embedding)
        self.index.build(self.n_trees)
        self.index.save(self.db_file_path)

    def add_items(self, embeddings, ids):
        """
        Add new items to the existing index.
        If the index does not exist, it will be built first.
        Saves the index to disk after adding the items.
        
        Args:
            embeddings (np.ndarray): The embeddings to add to the index.
            ids (List[int]): The IDs of the embeddings.

        Returns: None    
        """
        # Check if the index file exists, build initial index if not
        if not os.path.exists(self.db_file_path):
            self._build_initial_index(embeddings, ids)
        else:
            # Load existing index, add new items, and save the index
            self.index.load(self.db_file_path)
            for embedding, id in zip(embeddings, ids):
                self.index.add_item(id, embedding)
            self.index.save(self.db_file_path)
            
    def item_count(self):
        self.index.get_n_items()
                        