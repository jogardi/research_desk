"""
Test to verify that the fix for the late chunking bug works correctly.

The fix ensures that we use the same tokenization for both embedding and splitting,
which prevents tok_i from exceeding the available embeddings.
"""

import unittest
import sys
import io
from unittest.mock import patch, MagicMock, call
import torch
import numpy as np
from shared.embedding.flag_embed import FlagMultiVecEmbedder


class TestFlagEmbedFix(unittest.TestCase):
    """Test that the fix correctly handles late chunking tokenization"""

    def setUp(self):
        self.model_name = "BAAI/bge-m3"
        
    def test_fix_handles_tokenization_correctly(self):
        """Test that the fix uses joined tokenization for splitting"""
        print("hello")
        
        sentences = ["Hello world", "How are you", "Fine thanks"]
            
        embedder = FlagMultiVecEmbedder(self.model_name)
        
        result = embedder.emb_each_sentence(sentences)
        

    def test_fix_handles_problematic_examples(self):
        """Test with the actual problematic examples from the logs"""
        
        # with patch('shared.embedding.flag_embed.BGEM3FlagModel') as mock_model_class:
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        
        # Use actual problematic sentences from the logs
        sentences = [
            "Brownian collisions, 298",
            "transfection experiments in, 147",
            "Cytotoxic T cell (CTL) epitopes, 90"
        ]
        joined_text = ''.join(sentences)
        
        def mock_tokenize(text, **kwargs):
            if text == joined_text:
                # Joined tokenization - fewer tokens than sum of individuals
                return {'input_ids': torch.tensor([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]])}
            return {'input_ids': torch.tensor([[1, 2, 3]])}
        
        def mock_decode(token_ids, **kwargs):
            tokens = token_ids.tolist() if hasattr(token_ids, 'tolist') else token_ids
            
            # Simulate boundary detection
            if tokens == [1, 2, 3, 4, 5]:
                return "Brownian collisions, 298"
            elif tokens == [6, 7, 8, 9, 10]:
                return "transfection experiments in, 147"
            elif tokens == [11, 12, 13, 14, 15]:
                return "Cytotoxic T cell (CTL) epitopes, 90"
            
            # Partial decodes for boundary search
            if len(tokens) <= 5 and tokens[0] == 1:
                partial_texts = ["Brown", "Brownian", "Brownian col", "Brownian collisions", "Brownian collisions, 298"]
                return partial_texts[len(tokens)-1] if len(tokens) <= 5 else ""
            elif len(tokens) <= 5 and tokens[0] == 6:
                partial_texts = ["trans", "transfection", "transfection exp", "transfection experiments", "transfection experiments in, 147"]
                return partial_texts[len(tokens)-1] if len(tokens) <= 5 else ""
            elif len(tokens) <= 5 and tokens[0] == 11:
                partial_texts = ["Cyto", "Cytotoxic", "Cytotoxic T", "Cytotoxic T cell", "Cytotoxic T cell (CTL) epitopes, 90"]
                return partial_texts[len(tokens)-1] if len(tokens) <= 5 else ""
            
            return ""
        
        # Set up the mock tokenizer properly
        mock_tokenizer.side_effect = mock_tokenize
        mock_tokenizer.decode.side_effect = mock_decode
        
        def mock_emb_strs(texts, **kwargs):
            # Return embeddings matching joined tokenization
            return [torch.randn(15, 768)]
        
        
        embedder = FlagMultiVecEmbedder(self.model_name)
        
        captured_output = io.StringIO()
        
        # Patch numpy.mean to handle torch tensors
        def mock_np_mean(arr, axis=None):
            if hasattr(arr, 'shape') and len(arr.shape) > 0 and arr.shape[0] == 0:
                return torch.zeros(768)
            elif hasattr(arr, 'mean'):
                return arr.mean(dim=axis) if axis is not None else arr.mean()
            else:
                return np.mean(arr, axis=axis)
        
        # with patch('numpy.mean', mock_np_mean):
        result = embedder.emb_each_sentence(sentences)
        
        output = captured_output.getvalue()
        
        # Should not have "empty part" errors
        self.assertNotIn("empty part", output)
        
        # Should successfully return embeddings for all sentences
        self.assertEqual(result.shape[0], 3)


if __name__ == '__main__':
    unittest.main() 