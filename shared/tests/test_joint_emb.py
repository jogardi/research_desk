import unittest
from shared.embedding.joint_emb import JointSentenceEmbedder
from transformers import AutoTokenizer, AutoModel
import torch

def cosine_similarity(a, b):
    return torch.nn.functional.cosine_similarity(a, b)

class TestSentenceEmbedder(unittest.TestCase):

    def setUp(self):
        """Set up the SentenceEmbedder instance for testing."""
        self.embedder = JointSentenceEmbedder('sentence-transformers/all-MiniLM-L6-v2')


    def test_emb_toks(self):
        """Test the emb_toks method with dummy input."""
        dummy_toks = torch.randint(0, 100, (1, 10))
        token_embeddings = self.embedder.emb_toks(dummy_toks)
        self.assertIsInstance(token_embeddings, torch.Tensor)
        self.assertEqual(token_embeddings.shape[:2], dummy_toks.shape)  # Match sequence length

    def test_strs_to_toks_with_instruct(self):
        """Test the strs_to_toks_with_instruct method with sample queries."""
        queries = ["What is the capital of France?", "Define machine learning."]
        toks = self.embedder.strs_to_toks_with_instruct(queries)
        self.assertEqual(toks.shape[0], len(queries))

    def test_emb_strs(self):
        """Test the emb_strs method with sample text."""
        texts = ["What is the capital of France?", "Define machine learning."]
        embeddings = self.embedder.emb_strs(texts)
        self.assertIsInstance(embeddings, torch.Tensor)

    def test_emb_query(self):
        """Test the emb_query method with a single query."""
        query = "What is the capital of France?"
        query_embedding = self.embedder.emb_query(query)
        self.assertIsInstance(query_embedding, torch.Tensor)    

    def test_similarity_between_similar_strings(self):
        """Test embeddings of similar strings to ensure high similarity."""
        string1 = "The Eiffel Tower is in Paris."
        string2 = "The famous Eiffel Tower is located in Paris."
        embedding1 = self.embedder.emb_query(string1)
        embedding2 = self.embedder.emb_query(string2)

        similarity = cosine_similarity(embedding1.unsqueeze(0), embedding2.unsqueeze(0)).item()
        self.assertGreater(similarity, 0.8, "Similarity between similar strings is too low.")

    def test_similarity_between_dissimilar_strings(self):
        """Test embeddings of dissimilar strings to ensure low similarity."""
        string1 = "The Eiffel Tower is in Paris."
        string2 = "Cats are great pets."
        embedding1, embedding2 = self.embedder.emb_strs([string1, string2])

        similarity = cosine_similarity(embedding1.unsqueeze(0), embedding2.unsqueeze(0)).item()
        self.assertLess(similarity, 0.5, "Similarity between dissimilar strings is too high.")

    def test_similarity_between_identical_strings(self):
        """Test embeddings of identical strings to ensure perfect similarity."""
        string1 = "The Eiffel Tower is in Paris."
        string2 = "The Eiffel Tower is in Paris."
        embedding1, embedding2 = self.embedder.emb_strs([string1, string2])

        similarity = cosine_similarity(embedding1.unsqueeze(0), embedding2.unsqueeze(0)).item()
        self.assertAlmostEqual(similarity, 1.0, places=2, msg="Similarity between identical strings is not close to 1.")

    def test_emb_each_sentence(self):
        self.embedder.emb_strs(["The Eiffel Tower is in Paris.", "Cats are great pets."])

    

