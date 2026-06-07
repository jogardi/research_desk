"""
Unit tests for calling the Gemini API with litellm.
Tests both text-only and vision completions.
"""
import unittest
import dotenv
import litellm

# Load environment variables for API keys
dotenv.load_dotenv()


class TestLitellmGemini(unittest.TestCase):
    """Test litellm integration with Google Gemini models."""

    def setUp(self):
        """Set up test fixtures."""
        # Use the Gemini model configured in hparams
        self.gemini_model = "gemini/gemini-2.0-flash"
    
    def test_gemini_text_completion(self):
        """Test basic text completion with Gemini via litellm."""
        response = litellm.completion(
            model=self.gemini_model,
            messages=[
                {"role": "user", "content": "What is 2 + 2? Reply with just the number."}
            ],
            max_tokens=10,
            temperature=0.0
        )
        
        # Verify response structure
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.choices)
        self.assertGreater(len(response.choices), 0)
        
        # Check that we got a valid response
        content = response.choices[0].message.content
        self.assertIsNotNone(content)
        self.assertTrue(content.strip())  # Not empty
        
        # The answer should contain "4"
        self.assertIn("4", content)
        
        # Check usage stats are present
        self.assertIsNotNone(response.usage)
        self.assertGreater(response.usage.prompt_tokens, 0)
        self.assertGreater(response.usage.completion_tokens, 0)
        
        print(f"✅ Text completion response: {content}")
        print(f"   Tokens used: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}")

    def test_gemini_vision_completion(self):
        """Test vision completion with Gemini via litellm using a base64 image."""
        import base64
        from io import BytesIO
        from PIL import Image
        
        # Create a simple test image (red square with "TEST" text)
        img = Image.new('RGB', (100, 100), color='red')
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Call Gemini with vision
        response = litellm.completion(
            model=self.gemini_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        },
                        {
                            "type": "text",
                            "text": "What color is this image? Reply with just the color name."
                        }
                    ]
                }
            ],
            max_tokens=20,
            temperature=0.0
        )
        
        # Verify response structure
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.choices)
        self.assertGreater(len(response.choices), 0)
        
        # Check that we got a valid response
        content = response.choices[0].message.content
        self.assertIsNotNone(content)
        self.assertTrue(content.strip())  # Not empty
        
        # The answer should mention red
        self.assertIn("red", content.lower())
        
        print(f"✅ Vision completion response: {content}")
        print(f"   Tokens used: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}")

    def test_gemini_completion_with_retries(self):
        """Test completion_with_retries function with Gemini."""
        response = litellm.completion_with_retries(
            model=self.gemini_model,
            messages=[
                {"role": "user", "content": "Say 'hello world' in Python code. Just the code, no explanation."}
            ],
            max_tokens=50,
            temperature=0.0
        )
        
        # Verify response
        self.assertIsNotNone(response)
        content = response.choices[0].message.content
        self.assertIsNotNone(content)
        
        # Should contain print statement
        self.assertIn("print", content.lower())
        
        print(f"✅ Completion with retries response: {content}")


if __name__ == '__main__':
    unittest.main()

