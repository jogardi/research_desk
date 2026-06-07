"""
Tests for reproducing the "empty part" bug in FlagMultiVecEmbedder.emb_each_sentence

This bug occurs due to a tokenization mismatch in the emb_each_sentence method:

1. The method joins all input sentences into a single string: ''.join(sentences)
2. It gets embeddings for this joined string using emb_strs()
3. It then tries to split the embeddings back by tokenizing each sentence individually
4. However, the tokenization of the joined string differs from the sum of individual tokenizations
5. This causes the slicing (output[tok_i:tok_i+ntoks]) to be incorrect, resulting in empty parts

The bug manifests as "empty part" messages being printed when len(part) == 0.

Example from real logs:
- "empty part Brownian collisions, 298 7 154"
- "empty part transfection experiments in, 147 9 203"

The correct approach would be to embed each sentence individually, like the API implementation does.
"""

import unittest
import os
import sys
import io
from unittest.mock import patch, MagicMock
import torch
import numpy as np
from shared.embedding.flag_embed import FlagMultiVecEmbedder


class TestFlagEmbedEmptyPartBug(unittest.TestCase):
    """Test to reproduce the 'empty part' bug in FlagMultiVecEmbedder.emb_each_sentence"""

    def setUp(self):
        """Set up test environment"""
        # Use a lightweight model for testing
        self.model_name = "BAAI/bge-m3"
        
    def test_empty_part_bug_direct(self):
        """Test that directly reproduces the empty part bug"""
        
        with patch('shared.embedding.flag_embed.BGEM3FlagModel') as mock_model_class:
            mock_model = MagicMock()
            mock_tokenizer = MagicMock()
            
            # Create a scenario that will definitely cause empty parts
            def mock_tokenize(text, **kwargs):
                # First sentence: 3 tokens
                if text == "sentence one":
                    result = {'input_ids': torch.tensor([[1, 2, 3]])}
                # Second sentence: 2 tokens  
                elif text == "sentence two":
                    result = {'input_ids': torch.tensor([[4, 5]])}
                # Third sentence: 4 tokens
                elif text == "sentence three long":
                    result = {'input_ids': torch.tensor([[6, 7, 8, 9]])}
                # Joined text (what emb_strs gets)
                elif text == "sentence onesentence twosentence three long":
                    result = {'input_ids': torch.tensor([[1, 2, 3, 4, 5, 6, 7, 8, 9]])}
                else:
                    result = {'input_ids': torch.tensor([[1]])}
                return result
            
            mock_tokenizer.__call__ = mock_tokenize
            mock_model.tokenizer = mock_tokenizer
            
            # Mock emb_strs to return fewer embeddings than expected
            def mock_emb_strs(texts, **kwargs):
                # Expected: 3 + 2 + 4 = 9 embeddings based on individual tokenization
                # But return only 5 embeddings, causing empty parts for later sentences
                return [torch.randn(5, 768)]
            
            mock_model_class.return_value = mock_model
            
            embedder = FlagMultiVecEmbedder(self.model_name)
            embedder.emb_strs = mock_emb_strs
            
            test_sentences = [
                "sentence one",      # tok_i=0, ntoks=3, part=output[0:3] ✓
                "sentence two",      # tok_i=3, ntoks=2, part=output[3:5] ✓  
                "sentence three long" # tok_i=5, ntoks=4, part=output[5:9] ✗ (only 5 embeddings available)
            ]
            
            captured_output = io.StringIO()
            
            # Patch numpy.mean to handle empty tensors gracefully like the real scenario
            def mock_np_mean(arr, axis=None):
                if hasattr(arr, 'shape') and len(arr.shape) > 0 and arr.shape[0] == 0:
                    # Return a zero vector for empty parts (like the real code might do)
                    return torch.zeros(768)
                elif hasattr(arr, 'mean'):
                    # Use torch mean for torch tensors
                    return arr.mean(dim=axis) if axis is not None else arr.mean()
                else:
                    # Fall back to original numpy mean
                    return np.mean(arr, axis=axis)
            
            with patch('sys.stdout', captured_output), \
                 patch('numpy.mean', mock_np_mean):
                try:
                    result = embedder.emb_each_sentence(test_sentences)
                except Exception as e:
                    # The bug might cause exceptions due to empty tensors
                    pass
            
            output = captured_output.getvalue()
            self.assertIn("empty part", output,
                         "Expected 'empty part' message indicating the bug was reproduced")

    def test_empty_part_bug_with_zero_tokens(self):
        """Test the bug when tokenization returns 0 tokens"""
        
        with patch('shared.embedding.flag_embed.BGEM3FlagModel') as mock_model_class:
            mock_model = MagicMock()
            mock_tokenizer = MagicMock()
            
            def mock_tokenize(text, **kwargs):
                if text == "normal sentence":
                    return {'input_ids': torch.tensor([[1, 2, 3]])}
                elif text == "":
                    # Empty string results in 0 tokens
                    return {'input_ids': torch.tensor([[]])}
                else:
                    return {'input_ids': torch.tensor([[1]])}
            
            mock_tokenizer.__call__ = mock_tokenize
            mock_model.tokenizer = mock_tokenizer
            
            def mock_emb_strs(texts, **kwargs):
                return [torch.randn(3, 768)]
            
            mock_model_class.return_value = mock_model
            
            embedder = FlagMultiVecEmbedder(self.model_name)
            embedder.emb_strs = mock_emb_strs
            
            test_sentences = [
                "normal sentence",  # 3 tokens
                ""                  # 0 tokens -> empty part
            ]
            
            captured_output = io.StringIO()
            
            # Patch numpy.mean to handle empty tensors gracefully
            def mock_np_mean(arr, axis=None):
                if hasattr(arr, 'shape') and len(arr.shape) > 0 and arr.shape[0] == 0:
                    return torch.zeros(768)
                elif hasattr(arr, 'mean'):
                    return arr.mean(dim=axis) if axis is not None else arr.mean()
                else:
                    return np.mean(arr, axis=axis)
            
            with patch('sys.stdout', captured_output), \
                 patch('numpy.mean', mock_np_mean):
                try:
                    result = embedder.emb_each_sentence(test_sentences)
                except Exception as e:
                    pass
            
            output = captured_output.getvalue()
            self.assertIn("empty part", output,
                         "Expected 'empty part' message for zero-token sentence")

    def test_empty_part_bug_realistic_scenario(self):
        """Test with realistic sentences that could cause the bug"""
        
        with patch('shared.embedding.flag_embed.BGEM3FlagModel') as mock_model_class:
            mock_model = MagicMock()
            mock_tokenizer = MagicMock()
            
            def mock_tokenize(text, **kwargs):
                # Simulate real tokenization counts from the error log
                token_counts = {
                    "Brownian collisions, 298": 7,
                    "transfection experiments in, 147": 9,
                    "Cytotoxic T cell (CTL) epitopes, 90": 15,
                    "immune response, 91": 5,
                    "colipid, 143": 4,
                }
                
                count = token_counts.get(text, 3)
                return {'input_ids': torch.tensor([list(range(count))])}
            
            mock_tokenizer.__call__ = mock_tokenize
            mock_model.tokenizer = mock_tokenizer
            
            def mock_emb_strs(texts, **kwargs):
                # Return fewer embeddings than the sum of individual tokenizations
                # This simulates the tokenization mismatch issue
                return [torch.randn(10, 768)]  # Only 10 embeddings
            
            mock_model_class.return_value = mock_model
            
            embedder = FlagMultiVecEmbedder(self.model_name)
            embedder.emb_strs = mock_emb_strs
            
            # These sentences expect 7+9+15 = 31 tokens, but we only provide 10 embeddings
            test_sentences = [
                "Brownian collisions, 298",           # tok_i=0, needs 7 tokens
                "transfection experiments in, 147",   # tok_i=7, needs 9 tokens  
                "Cytotoxic T cell (CTL) epitopes, 90" # tok_i=16, needs 15 tokens (but only 10 available)
            ]
            
            captured_output = io.StringIO()
            
            # Patch numpy.mean to handle empty tensors gracefully
            def mock_np_mean(arr, axis=None):
                if hasattr(arr, 'shape') and len(arr.shape) > 0 and arr.shape[0] == 0:
                    return torch.zeros(768)
                elif hasattr(arr, 'mean'):
                    return arr.mean(dim=axis) if axis is not None else arr.mean()
                else:
                    return np.mean(arr, axis=axis)
            
            with patch('sys.stdout', captured_output), \
                 patch('numpy.mean', mock_np_mean):
                try:
                    result = embedder.emb_each_sentence(test_sentences)
                except Exception as e:
                    pass
            
            output = captured_output.getvalue()
            self.assertIn("empty part", output,
                         "Expected 'empty part' message from realistic tokenization mismatch")


if __name__ == '__main__':
    unittest.main() 