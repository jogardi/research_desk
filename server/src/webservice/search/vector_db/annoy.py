import annoy
from webservice.search.vector_db._interface import VectorDB

class AnnoyVectorDB(VectorDB):
    def __init__(self, db_file_path: str, dim: int, n_trees=10, metric='angular'):
        self.index = annoy.AnnoyIndex(dim, metric)
        self.db_file_path = db_file_path
        self.n_trees = n_trees
                        
    def load(self, category):
        self.index.load(self.db_file_path)

    def retrieve(self, query_embedding, k=10):
        # nearest_ids, distances = self.index.get_nns_by_vector(query_embedding, n_neighbors=k, include_distances = True)
        nearest_ids, distances = self.index.get_nns_by_vector(query_embedding, n=k, include_distances=True)

        # convert distances cosine similarity score values between 0 and 1:
        similarity_scores = [1 - distance**2 / 2 for distance in distances]
        
        return nearest_ids, similarity_scores