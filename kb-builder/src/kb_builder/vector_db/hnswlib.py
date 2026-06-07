import hnswlib
import os
if 'kb-builder' in os.getcwd():
    from kb_builder.vector_db._interface import VectorDB
else:
    from vector_db._interface import VectorDB

from kb_builder.hparams_config import hpc
from shared.hparams_config import hpc as shared_hpc

from shared.config import Config

class HnswlibVectorDB(VectorDB):
    def __init__(self, db_file_path: str, dim: int):
        """Initialize the database instance with the given database file path."""
        self.index = hnswlib.Index(space='cosine', dim=dim) # initialize the index
        self.db_file_path = db_file_path # set the database file path

    def _build_initial_index(self, embeddings, ids):
        """Build the initial index with the provided embeddings and ids."""
        self.index.init_index(max_elements=shared_hpc().HNSWLIB_MAX_ELEMENTS, ef_construction=shared_hpc().HNSWLIB_EF_CONSTRUCTION, M=shared_hpc().HNSWLIB_M)
        self.index.add_items(embeddings, ids)
        self.index.save_index(self.db_file_path)

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
            self.index.load_index(self.db_file_path, max_elements=shared_hpc().HNSWLIB_MAX_ELEMENTS)
            self.index.add_items(embeddings, ids)
            self.index.save_index(self.db_file_path)
            
    def item_count(self):
        """
        Count the number of items in the index.
        
        Returns:
            int: The number of items in the index.
        """
        self.index.load_index(self.db_file_path, max_elements=shared_hpc().HNSWLIB_MAX_ELEMENTS)
        return self.index.element_count
