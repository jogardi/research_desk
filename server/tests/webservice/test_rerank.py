"""
Unit tests for reranking functionality, including FlashRank implementation.
"""
import unittest
from unittest.mock import patch, MagicMock
import numbers
import sys
from webservice.llm.together.rerank import Reranker


class TestReranker(unittest.TestCase):
    """Test cases for the Reranker class."""

    def setUp(self):
        """Set up test fixtures."""
        self.reranker = Reranker(model="test-model")
        self.test_query = "How to improve machine learning performance?"
        self.test_documents = [
            "Machine learning optimization techniques include feature selection and hyperparameter tuning.",
            "Deep learning models require careful architecture design and regularization.",
            "Data preprocessing is crucial for machine learning success.",
            "Cross-validation helps evaluate model performance accurately.",
            "Ensemble methods can improve prediction accuracy."
        ]

    def test_flashrank_success(self):
        """Test successful FlashRank reranking."""
        # Mock FlashRank components
        mock_ranker = MagicMock()
        mock_rerank_request = MagicMock()
        
        # Mock the return value from FlashRank
        mock_results = [
            {"id": 0, "score": 0.95},
            {"id": 2, "score": 0.87},
            {"id": 1, "score": 0.82},
            {"id": 3, "score": 0.78},
            {"id": 4, "score": 0.65}
        ]
        mock_ranker.rerank.return_value = mock_results
        
        with patch('flashrank.Ranker', return_value=mock_ranker) as mock_ranker_class:
            with patch('flashrank.RerankRequest', return_value=mock_rerank_request) as mock_request_class:
                result = self.reranker.flashrank(self.test_query, self.test_documents)
                
                # Verify FlashRank was initialized correctly
                mock_ranker_class.assert_called_once_with(max_length=512)
                
                # Verify RerankRequest was created correctly
                mock_request_class.assert_called_once()
                call_args = mock_request_class.call_args
                self.assertEqual(call_args[1]['query'], self.test_query)
                
                # Verify passages format
                passages = call_args[1]['passages']
                self.assertEqual(len(passages), len(self.test_documents))
                for i, passage in enumerate(passages):
                    self.assertEqual(passage['id'], i)
                    self.assertEqual(passage['text'], self.test_documents[i])
                    self.assertEqual(passage['meta']['index'], i)
                
                # Verify rerank was called
                mock_ranker.rerank.assert_called_once_with(mock_rerank_request)
                
                # Verify result format
                self.assertEqual(len(result), len(mock_results))
                for i, res in enumerate(result):
                    self.assertIn('index', res)
                    self.assertIn('score', res)
                    self.assertEqual(res['index'], mock_results[i]['id'])
                    self.assertEqual(res['score'], mock_results[i]['score'])

    def test_flashrank_empty_documents(self):
        """Test FlashRank with empty document list."""
        result = self.reranker.flashrank(self.test_query, [])
        self.assertEqual(result, [])

    def test_flashrank_import_error(self):
        """Test FlashRank when the library is not installed."""
        # Mock the import to raise ImportError at the module level
        with patch.dict('sys.modules', {'flashrank': None}):
            with patch('builtins.print') as mock_print:
                result = self.reranker.flashrank(self.test_query, self.test_documents)
                
                # Verify error message was printed (could be either message depending on timing)
                print_calls = [call.args[0] for call in mock_print.call_args_list]
                self.assertTrue(any("FlashRank not installed" in call or "FlashRank" in call for call in print_calls))
                
                # Verify fallback result
                self.assertEqual(len(result), len(self.test_documents))
                for i, res in enumerate(result):
                    self.assertEqual(res['index'], i)
                    self.assertEqual(res['score'], -1.0)

    def test_flashrank_runtime_exception(self):
        """Test FlashRank handling of runtime exceptions."""
        mock_ranker = MagicMock()
        mock_ranker.rerank.side_effect = Exception("FlashRank processing error")
        
        with patch('flashrank.Ranker', return_value=mock_ranker):
            with patch('flashrank.RerankRequest'):
                with patch('builtins.print') as mock_print:
                    result = self.reranker.flashrank(self.test_query, self.test_documents)
                    
                    # Verify error message was printed
                    mock_print.assert_called_with("*** RANKER FlashRank Exception: FlashRank processing error")
                    
                    # Verify fallback result
                    self.assertEqual(len(result), len(self.test_documents))
                    for i, res in enumerate(result):
                        self.assertEqual(res['index'], i)
                        self.assertEqual(res['score'], -1.0)

    def test_flashrank_integration_with_actual_library(self):
        """Integration test with actual FlashRank library (if available)."""
        try:
            from flashrank import Ranker, RerankRequest
            
            # Test with a small subset of documents to avoid long test times
            small_documents = self.test_documents[:3]
            result = self.reranker.flashrank(self.test_query, small_documents)
            
            # Verify basic structure
            self.assertEqual(len(result), len(small_documents))
            for res in result:
                self.assertIn('index', res)
                self.assertIn('score', res)
                self.assertIsInstance(res['index'], int)
                self.assertIsInstance(res['score'], numbers.Number)
                self.assertTrue(0 <= res['index'] < len(small_documents))
            
            # Verify results are sorted by score (descending)
            scores = [res['score'] for res in result]
            self.assertEqual(scores, sorted(scores, reverse=True))
            
            print(f"✅ FlashRank integration test passed with {len(result)} results")
            
        except ImportError:
            self.skipTest("FlashRank not installed - skipping integration test")

    def test_flashrank_consistency(self):
        """Test that FlashRank produces consistent results."""
        try:
            from flashrank import Ranker, RerankRequest
            
            # Run the same query twice
            result1 = self.reranker.flashrank(self.test_query, self.test_documents)
            result2 = self.reranker.flashrank(self.test_query, self.test_documents)
            
            # Results should be identical for the same input
            self.assertEqual(len(result1), len(result2))
            for r1, r2 in zip(result1, result2):
                self.assertEqual(r1['index'], r2['index'])
                self.assertAlmostEqual(r1['score'], r2['score'], places=6)
            
            print("✅ FlashRank consistency test passed")
            
        except ImportError:
            self.skipTest("FlashRank not installed - skipping consistency test")

    def test_flashrank_different_queries(self):
        """Test FlashRank with different types of queries."""
        try:
            from flashrank import Ranker, RerankRequest
            
            test_cases = [
                ("machine learning", self.test_documents),
                ("data preprocessing", self.test_documents),
                ("model evaluation", self.test_documents),
            ]
            
            for query, docs in test_cases:
                result = self.reranker.flashrank(query, docs)
                
                # Basic validation
                self.assertEqual(len(result), len(docs))
                self.assertTrue(all('index' in res and 'score' in res for res in result))
                
                # Scores should be sorted in descending order
                scores = [res['score'] for res in result]
                self.assertEqual(scores, sorted(scores, reverse=True))
            
            print("✅ FlashRank different queries test passed")
            
        except ImportError:
            self.skipTest("FlashRank not installed - skipping different queries test")


if __name__ == '__main__':
    unittest.main() 