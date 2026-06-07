import unittest
import os
from unittest.mock import Mock, patch
from kb_builder.vectorize.chunk_and_embed import chunk_and_embed

class TestVideoChunking(unittest.TestCase):

    def setUp(self):
        # Set the profile to avoid configuration errors
        os.environ['PROFILE'] = 'default'

    @patch('kb_builder.vectorize.chunker.non_agentic_split_text_by_sentence_and_tokens')
    def test_video_transcript_skips_agentic_chunking(self, mock_split):
        # Mock the model
        mock_model = Mock()
        mock_tokenizer = Mock()
        mock_model.get_tokenizer.return_value = mock_tokenizer
        mock_model.embed_many.return_value = [[0.1, 0.2], [0.3, 0.4]]
        
        # Mock the sentence splitter to return chunks
        mock_split.return_value = ["First sentence.", "Second sentence."]
        
        try:
            # Process a video transcript
            document = "First sentence. Second sentence."
            chunks, embeddings = chunk_and_embed(document, mock_model, "transcript")
            
            # Verify non_agentic_split_text_by_sentence_and_tokens was called
            mock_split.assert_called_once_with(document, mock_tokenizer, 2048)
            
            # Verify the chunks
            self.assertEqual(chunks, ("First sentence.", "Second sentence."))
            self.assertEqual(len(embeddings), 2)
            
        except Exception as e:
            print(f"Error: {e}")
            raise

    def test_video_transcript_always_uses_sentence_splitting(self):
        """Test that video transcripts always use sentence splitting regardless of configuration"""
        # Mock the model
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Mock the tokenizer to return proper encoding structure
        def mock_encode_plus(text, **kwargs):
            # Simple mock that returns one token per word
            words = text.split()
            offsets = []
            current_pos = 0
            for word in words:
                start = text.find(word, current_pos)
                end = start + len(word)
                offsets.append((start, end))
                current_pos = end
            return {"offset_mapping": offsets}
        
        mock_tokenizer.encode_plus.side_effect = mock_encode_plus
        mock_model.get_tokenizer.return_value = mock_tokenizer
        mock_model.embed_many.return_value = [[0.1, 0.2]]
        
        # Test with a transcript that would normally be chunked by agentic chunking
        document = "This is a test transcript with multiple sentences. It should be split into chunks."
        
        try:
            chunks, embeddings = chunk_and_embed(document, mock_model, "transcript")
            
            # Verify it was processed (exact chunks depend on sentence splitter)
            self.assertIsInstance(chunks, tuple)
            self.assertGreater(len(chunks), 0)
            self.assertEqual(len(chunks), len(embeddings))
            
            # Verify the model was called to embed
            mock_model.embed_many.assert_called_once()
            
        except Exception as e:
            print(f"Error: {e}")
            raise

if __name__ == '__main__':
    unittest.main() 
