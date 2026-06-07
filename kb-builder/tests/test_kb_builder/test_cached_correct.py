"""
Unit tests for AgenticCorrectCache to verify caching prevents duplicate calls.
"""

import json
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from kb_builder.pre_processor.cached_correct import (
    AgenticCorrectCache,
    get_cached_completion,
    cache_completion,
    clear_cache,
    cache_size,
)


class TestAgenticCorrectCache(unittest.TestCase):
    """Test cases for AgenticCorrectCache class."""
    
    def setUp(self):
        """Set up test fixtures with temporary cache directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "test_cache"
        self.cache = AgenticCorrectCache(cache_dir=self.cache_dir)
        
        # Sample test data
        self.test_messages = [
            {"role": "user", "content": "Test message 1"},
            {"role": "assistant", "content": "Test response 1"}
        ]
        self.test_model = "gpt-4"
        self.test_temperature = 0.7
        self.test_response = {"choices": [{"message": {"content": "Test completion"}}]}
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently."""
        key1 = self.cache._get_cache_key(self.test_messages, self.test_model, self.test_temperature)
        key2 = self.cache._get_cache_key(self.test_messages, self.test_model, self.test_temperature)
        
        self.assertEqual(key1, key2)
        self.assertIsInstance(key1, str)
        self.assertEqual(len(key1), 64)  # SHA256 hash length
    
    def test_cache_key_uniqueness(self):
        """Test that different inputs generate different cache keys."""
        key1 = self.cache._get_cache_key(self.test_messages, self.test_model, self.test_temperature)
        
        # Different messages
        different_messages = [{"role": "user", "content": "Different message"}]
        key2 = self.cache._get_cache_key(different_messages, self.test_model, self.test_temperature)
        
        # Different model
        key3 = self.cache._get_cache_key(self.test_messages, "gpt-3.5-turbo", self.test_temperature)
        
        # Different temperature
        key4 = self.cache._get_cache_key(self.test_messages, self.test_model, 0.5)
        
        self.assertNotEqual(key1, key2)
        self.assertNotEqual(key1, key3)
        self.assertNotEqual(key1, key4)
    
    def test_cache_miss_returns_none(self):
        """Test that cache miss returns None."""
        result = self.cache.get(self.test_messages, self.test_model, self.test_temperature)
        self.assertIsNone(result)
    
    def test_cache_hit_returns_stored_value(self):
        """Test that cache hit returns the stored value."""
        # Store a value
        self.cache.set(self.test_messages, self.test_model, self.test_temperature, self.test_response)
        
        # Retrieve it
        result = self.cache.get(self.test_messages, self.test_model, self.test_temperature)
        
        self.assertEqual(result, self.test_response)
    
    def test_cache_prevents_duplicate_calls(self):
        """Test that cache prevents duplicate API calls."""
        call_count = 0
        
        def mock_api_call(messages, model_name, temperature):
            nonlocal call_count
            call_count += 1
            return {"call_number": call_count, "content": f"Response {call_count}"}
        
        # Simulate first call (cache miss)
        cached_result = self.cache.get(self.test_messages, self.test_model, self.test_temperature)
        self.assertIsNone(cached_result)
        
        # Make the "API call" and cache the result
        api_response = mock_api_call(self.test_messages, self.test_model, self.test_temperature)
        self.cache.set(self.test_messages, self.test_model, self.test_temperature, api_response)
        
        # Verify first call was made
        self.assertEqual(call_count, 1)
        self.assertEqual(api_response["call_number"], 1)
        
        # Simulate second call (should be cache hit)
        cached_result = self.cache.get(self.test_messages, self.test_model, self.test_temperature)
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result["call_number"], 1)  # Should be the cached result
        
        # Verify no additional API call was made
        self.assertEqual(call_count, 1)
    
    def test_cache_file_persistence(self):
        """Test that cache persists to disk and can be reloaded."""
        # Store a value
        self.cache.set(self.test_messages, self.test_model, self.test_temperature, self.test_response)
        
        # Create a new cache instance with the same directory
        new_cache = AgenticCorrectCache(cache_dir=self.cache_dir)
        
        # Should retrieve the cached value
        result = new_cache.get(self.test_messages, self.test_model, self.test_temperature)
        self.assertEqual(result, self.test_response)
    
    def test_cache_size_tracking(self):
        """Test that cache size is tracked correctly."""
        self.assertEqual(self.cache.size(), 0)
        
        # Add one entry
        self.cache.set(self.test_messages, self.test_model, self.test_temperature, self.test_response)
        self.assertEqual(self.cache.size(), 1)
        
        # Add another entry with different parameters
        different_messages = [{"role": "user", "content": "Different message"}]
        self.cache.set(different_messages, self.test_model, self.test_temperature, self.test_response)
        self.assertEqual(self.cache.size(), 2)
    
    def test_cache_clear(self):
        """Test that cache can be cleared."""
        # Add some entries
        self.cache.set(self.test_messages, self.test_model, self.test_temperature, self.test_response)
        self.assertEqual(self.cache.size(), 1)
        
        # Clear cache
        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)
        
        # Verify entry is no longer retrievable
        result = self.cache.get(self.test_messages, self.test_model, self.test_temperature)
        self.assertIsNone(result)
    
    def test_corrupted_cache_file_handling(self):
        """Test that corrupted cache files are handled gracefully."""
        # Create a corrupted cache file
        cache_key = self.cache._get_cache_key(self.test_messages, self.test_model, self.test_temperature)
        cache_path = self.cache._get_cache_path(cache_key)
        
        # Write invalid pickle data
        with open(cache_path, 'wb') as f:
            f.write(b'invalid pickle data')
        
        # Should return None and remove the corrupted file
        result = self.cache.get(self.test_messages, self.test_model, self.test_temperature)
        self.assertIsNone(result)
        self.assertFalse(cache_path.exists())
    
    def test_global_cache_functions(self):
        """Test the global cache functions."""
        # Test cache miss
        result = get_cached_completion(self.test_messages, self.test_model, self.test_temperature)
        self.assertIsNone(result)
        
        # Cache a completion
        cache_completion(self.test_messages, self.test_model, self.test_temperature, self.test_response)
        
        # Test cache hit
        result = get_cached_completion(self.test_messages, self.test_model, self.test_temperature)
        self.assertEqual(result, self.test_response)
        
        # Test cache size
        self.assertGreaterEqual(cache_size(), 1)
        
        # Test clear cache
        clear_cache()
        result = get_cached_completion(self.test_messages, self.test_model, self.test_temperature)
        self.assertIsNone(result)
    
    def test_multiple_concurrent_requests_same_params(self):
        """Test that multiple requests with same parameters all get cached result."""
        call_count = 0
        
        def mock_expensive_operation(messages, model_name, temperature):
            nonlocal call_count
            call_count += 1
            return {"expensive_result": f"computed_{call_count}"}
        
        # Simulate the pattern of checking cache, then calling API if miss
        def simulate_completion_call(messages, model_name, temperature):
            # Check cache first
            cached = self.cache.get(messages, model_name, temperature)
            if cached is not None:
                return cached
            
            # Cache miss - make expensive call
            result = mock_expensive_operation(messages, model_name, temperature)
            
            # Cache the result
            self.cache.set(messages, model_name, temperature, result)
            return result
        
        # Make multiple calls with same parameters
        result1 = simulate_completion_call(self.test_messages, self.test_model, self.test_temperature)
        result2 = simulate_completion_call(self.test_messages, self.test_model, self.test_temperature)
        result3 = simulate_completion_call(self.test_messages, self.test_model, self.test_temperature)
        
        # Should only have made one expensive call
        self.assertEqual(call_count, 1)
        
        # All results should be identical
        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)
        self.assertEqual(result1["expensive_result"], "computed_1")
    
    def test_cache_with_complex_messages(self):
        """Test caching with complex message structures."""
        complex_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": "Analyze this image"},
                    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
                ]
            }
        ]
        
        # Test that complex structures can be cached
        self.cache.set(complex_messages, self.test_model, self.test_temperature, self.test_response)
        result = self.cache.get(complex_messages, self.test_model, self.test_temperature)
        
        self.assertEqual(result, self.test_response)
    
    def test_cache_directory_creation(self):
        """Test that cache directory is created if it doesn't exist."""
        non_existent_dir = Path(self.temp_dir) / "non_existent" / "cache"
        self.assertFalse(non_existent_dir.exists())
        
        # Creating cache should create the directory
        cache = AgenticCorrectCache(cache_dir=non_existent_dir)
        self.assertTrue(non_existent_dir.exists())
    
    def test_agentic_chunk_correct_usage_pattern(self):
        """Test the exact usage pattern from agentic_chunk_correct.py."""
        # Use our isolated cache instance instead of global cache
        api_call_count = 0
        
        def mock_completion_with_retries(messages, model, temperature):
            nonlocal api_call_count
            api_call_count += 1
            # Create a serializable response object that mimics the structure of litellm responses
            return {
                "choices": [
                    {
                        "message": {
                            "content": f"Corrected and chunked text {api_call_count}"
                        }
                    }
                ]
            }
        
        # Simulate the exact pattern from agentic_correct_and_chunk_page
        def simulate_agentic_correct_and_chunk_page(blocks_text, img_b64, model_name, temperature, page_num):
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        },
                        {"type": "text", "text": blocks_text}
                    ]
                }
            ]
            
            # Check cache first (exactly as in the real code) - use our isolated cache
            cached_response = self.cache.get(messages, model_name, temperature)
            if cached_response is not None:
                print(f"Using cached response for page {page_num}")
                response = cached_response
            else:
                print(f"Making API call for page {page_num}")
                response = mock_completion_with_retries(
                    messages=messages,
                    model=model_name,
                    temperature=temperature
                )
                # Cache the response - use our isolated cache
                self.cache.set(messages, model_name, temperature, response)
            
            return response["choices"][0]["message"]["content"]
        
        # Test data
        blocks_text = "Block 1 text\n==8529==\nBlock 2 text"
        img_b64 = "fake_base64_image_data"
        model_name = "gpt-4-vision-preview"
        temperature = 0.1
        
        # First call - should hit the API
        result1 = simulate_agentic_correct_and_chunk_page(
            blocks_text, img_b64, model_name, temperature, page_num=1
        )
        self.assertEqual(api_call_count, 1)
        self.assertEqual(result1, "Corrected and chunked text 1")
        
        # Second call with same parameters - should use cache
        result2 = simulate_agentic_correct_and_chunk_page(
            blocks_text, img_b64, model_name, temperature, page_num=1
        )
        self.assertEqual(api_call_count, 1)  # Should not increment
        self.assertEqual(result2, "Corrected and chunked text 1")  # Same result
        
        # Third call with different blocks - should hit API again
        different_blocks_text = "Different block text\n==8529==\nAnother block"
        result3 = simulate_agentic_correct_and_chunk_page(
            different_blocks_text, img_b64, model_name, temperature, page_num=2
        )
        self.assertEqual(api_call_count, 2)  # Should increment
        self.assertEqual(result3, "Corrected and chunked text 2")
        
        # Fourth call with same blocks as first - should use cache
        result4 = simulate_agentic_correct_and_chunk_page(
            blocks_text, img_b64, model_name, temperature, page_num=1
        )
        self.assertEqual(api_call_count, 2)  # Should not increment
        self.assertEqual(result4, "Corrected and chunked text 1")  # Same as first result


if __name__ == '__main__':
    unittest.main() 