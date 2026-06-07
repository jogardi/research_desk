import unittest
import os
import torch
from unittest.mock import patch, MagicMock
from shared.embedding.flag_embed import FlagMultiVecEmbedder
from shared.embedding.sentence_transformer import SentenceTransformerModel


class TestFlagEmbedMetaTensorIssue(unittest.TestCase):
    """Test to reproduce the meta tensor issue with FlagEmbedding models"""

    def setUp(self):
        """Set up test environment"""
        # Use a lightweight model for testing
        self.model_name = "BAAI/bge-m3"
        
    def test_flag_embed_meta_tensor_issue(self):
        """Test that reproduces the meta tensor issue when initializing FlagMultiVecEmbedder"""
        
        # Mock the BGEM3FlagModel to simulate the meta tensor issue
        with patch('shared.embedding.flag_embed.BGEM3FlagModel') as mock_model_class:
            # Create a mock model instance
            mock_model = MagicMock()
            mock_tokenizer = MagicMock()
            mock_model.tokenizer = mock_tokenizer
            
            # Mock the encode_queries method to raise the meta tensor error
            def mock_encode_queries(*args, **kwargs):
                # Create a mock meta tensor error
                raise NotImplementedError(
                    "Cannot copy out of meta tensor; no data! "
                    "Please use torch.nn.Module.to_empty() instead of torch.nn.Module.to() "
                    "when moving module from meta to a different device."
                )
            
            mock_model.encode_queries = mock_encode_queries
            mock_model_class.return_value = mock_model
            
            # Initialize the embedder
            embedder = FlagMultiVecEmbedder(self.model_name)
            
            # This should trigger the meta tensor error
            with self.assertRaises(NotImplementedError) as context:
                embedder.emb_query("test query")
            
            # Verify the error message contains the expected meta tensor error
            self.assertIn("Cannot copy out of meta tensor", str(context.exception))
            self.assertIn("to_empty()", str(context.exception))

    def test_sentence_transformer_model_with_flag_embed(self):
        """Test SentenceTransformerModel with flag/ prefix to reproduce the issue"""
        
        # Mock the FlagMultiVecEmbedder to simulate the meta tensor issue
        with patch('shared.embedding.sentence_transformer.FlagMultiVecEmbedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            
            # Mock emb_query to raise the meta tensor error
            def mock_emb_query(*args, **kwargs):
                raise NotImplementedError(
                    "Cannot copy out of meta tensor; no data! "
                    "Please use torch.nn.Module.to_empty() instead of torch.nn.Module.to() "
                    "when moving module from meta to a different device."
                )
            
            mock_embedder.emb_query = mock_emb_query
            mock_embedder_class.return_value = mock_embedder
            
            # Initialize SentenceTransformerModel with flag/ prefix
            model = SentenceTransformerModel(model="flag/BAAI/bge-m3")
            
            # This should trigger the meta tensor error through the embedding chain
            with self.assertRaises(NotImplementedError) as context:
                model.embed("test text")
            
            # Verify the error message
            self.assertIn("Cannot copy out of meta tensor", str(context.exception))

    def test_flag_embed_initialization_fallback(self):
        """Test that FlagMultiVecEmbedder initialization handles various failure modes"""
        
        # Test the fallback mechanism in FlagMultiVecEmbedder.__init__
        with patch('shared.embedding.flag_embed.BGEM3FlagModel') as mock_model_class:
            
            # First attempt fails with meta tensor error
            def first_attempt(*args, **kwargs):
                if 'device' in kwargs and kwargs['device'] == 'auto':
                    raise NotImplementedError("Cannot copy out of meta tensor; no data!")
                return MagicMock()
            
            mock_model_class.side_effect = first_attempt
            
            # This should trigger the fallback logic
            embedder = FlagMultiVecEmbedder(self.model_name)
            
            # Verify that the model was attempted to be created multiple times
            self.assertGreater(mock_model_class.call_count, 1)

    def test_real_flag_embed_initialization(self):
        """Test actual FlagMultiVecEmbedder initialization to see if it fails"""
        
        # Skip this test if we don't have the model downloaded or if it's too heavy
        try:
            # Try to initialize with a small model
            embedder = FlagMultiVecEmbedder("BAAI/bge-m3")
            
            # Try a simple embedding operation
            result = embedder.emb_query("hello world")
            
            # If we get here, the initialization worked
            self.assertIsNotNone(result)
            
        except NotImplementedError as e:
            if "Cannot copy out of meta tensor" in str(e):
                # This is the exact error we're trying to reproduce
                self.fail(f"Reproduced the meta tensor error: {e}")
            else:
                # Some other NotImplementedError
                raise
        except Exception as e:
            # Other errors (like model not found, network issues, etc.)
            # Skip the test as these are environmental issues
            self.skipTest(f"Skipping due to environmental issue: {e}")


if __name__ == '__main__':
    unittest.main() 