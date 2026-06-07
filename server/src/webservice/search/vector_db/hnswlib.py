

import hnswlib
from webservice.search.vector_db._interface import VectorDB
from shared.hparams_config import hpc as shared_hpc
from webservice.hparams_config import hpc
import numpy as np

def get_topk(xs: np.ndarray, k):
    # topk in sorted order
    indices = np.argpartition(xs, -k - 1)[-k:]
    results = []
    for index in indices:
        results.append((xs[index], index))
    results.sort(reverse=True)
    return np.array([index for _, index in results])


def exact_search(query_embedding, all_vectors, k):
    cos_sims = all_vectors @ np.array(query_embedding.T)

    # get top k
    top_k_indices = get_topk(cos_sims, k)
    return top_k_indices, cos_sims[top_k_indices].tolist()

class HnswlibVectorDB(VectorDB):
    def __init__(self, db_file_path: str, dim: int):
        """Initialize the database instance with the given database file path."""
        self.index = hnswlib.Index(space='cosine', dim=dim) # initialize the index
        self.db_file_path = db_file_path
                        
    def load(self):
        # self.index.load_index(self.db_file_path, max_elements=1000000)
        self.index.load_index(self.db_file_path, max_elements=shared_hpc().HNSWLIB_MAX_ELEMENTS)   
        if hpc().ENABLE_EXACT_SEARCH:
            all_ids = sorted(self.index.get_ids_list())
            # check that all_ids equals range(len(all_ids))
            assert all_ids == list(range(1, len(all_ids) + 1)), f"all_ids does not equal {all_ids[0]} {all_ids[-1]}"
            print("checked ids")
            self.all_vectors = self.index.get_items(all_ids)
        else:
            self.num_elements = self.index.get_current_count()

    def retrieve(self, query_embedding, k=10):
        if hpc().ENABLE_EXACT_SEARCH:
            idxs, scores = exact_search(query_embedding, self.all_vectors, k)
            return idxs + 1, scores
        else:
            labels, distances = self.index.knn_query(query_embedding, min(k, self.num_elements))
            print(f"num_elements: {self.num_elements}", len(distances), k)
            # convert distances cosine similarity score values between 0 and 1:
            similarity_scores = [float(1 - distance) for distance in distances[0]]
            return labels[0], similarity_scores    
