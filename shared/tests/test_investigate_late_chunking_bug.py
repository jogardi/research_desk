"""
Investigation of the late chunking bug in FlagMultiVecEmbedder.emb_each_sentence

The issue appears to be that tok_i (token index) grows beyond the available embeddings
from the joined text. This suggests that the sum of individual tokenizations exceeds
the tokenization of the joined text.

From the logs:
- empty part Brownian collisions, 298 7 154
- empty part transfection experiments in, 147 7 203

This means tok_i=154 and tok_i=203, which are very high indices.
"""

import unittest
import sys
import io
from shared.embedding.flag_embed import FlagMultiVecEmbedder


class TestLateChuningBugInvestigation(unittest.TestCase):
    """Investigate why late chunking causes tok_i to exceed available embeddings"""

    def setUp(self):
        self.model_name = "BAAI/bge-m3"
        
    def test_investigate_tokenization_mismatch(self):
        """Test to understand why tok_i exceeds available embeddings"""
        
        # Use real sentences from the error logs
        individual_sentences = [
            "Brownian collisions, 298",
            "transfection experiments in, 147", 
            "Cytotoxic T cell (CTL) epitopes, 90",
            "immune response, 91",
            "colipid, 143"
        ]
        
        embedder = FlagMultiVecEmbedder(self.model_name)
        
        try:
            result = embedder.emb_each_sentence(individual_sentences)
            print(f"Result shape: {result.shape}")
        except Exception as e:
            print(f"Exception: {e}")

    def test_demonstrate_root_cause(self):
        """Demonstrate that the root cause is sum(individual_tokenizations) > joined_tokenization"""
        
        # Simple example to clearly show the mismatch
        sentences = ["Hello world", "How are you", "Fine thanks"]
        
        embedder = FlagMultiVecEmbedder(self.model_name)
        
        result = embedder.emb_each_sentence(sentences)
        print(f"Simple example result shape: {result.shape}")


if __name__ == '__main__':
    unittest.main() 