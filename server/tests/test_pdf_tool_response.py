import pytest
import json
from unittest.mock import Mock, patch
from webservice.llm.agent_utils import LiteLLMChat
from dataclasses import dataclass
import dotenv
dotenv.load_dotenv()


@dataclass
class PdfUrl:
    """Represents a PDF URL for tool responses."""
    url: str

def test_pdf_tool_response_with_minimal_chat():
    """Test PDF tool response with a minimal chat implementation that avoids the web search issue."""
    import litellm
    pdf_url = "https://ontheline.trincoll.edu/images/bookdown/sample-local-pdf.pdf"
    
    def load_pdf_tool(pdf_url) -> list:
        """Load a PDF from the specified URL and return it in the format Claude expects."""
        return [
            {"type": "text", "text": f"Loading PDF from: {pdf_url}"},
        ]
    
    # Create tool schema manually
    tool_schema = {
        "type": "function",
        "function": {
            "name": "load_pdf_tool",
            "description": "Load a PDF from the specified URL and return it in the format Claude expects.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pdf_url": {
                        "type": "string",
                        "description": "URL of the PDF to load"
                    }
                },
                "required": ["pdf_url"]
            }
        }
    }
    
    # Initial messages
    messages = [
        {
            "role": "user", 
            "content": f"Please use the load_pdf_tool to load '{pdf_url}'and tell me what it's about."
        }
    ]
    
    try:
        # First API call - Claude decides to use the tool
        response = litellm.completion(
            model="anthropic/claude-sonnet-4-20250514",
            messages=messages,
            tools=[tool_schema],
            tool_choice="auto"
        )
        
        print("First response:", response.choices[0].message)
        
        # Check if Claude wants to use the tool
        if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            print("Tool call:", tool_call)
            
            # Add assistant message with tool call
            messages.append({
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                ]
            })
            
            # Execute the tool
            args = json.loads(tool_call.function.arguments)
            tool_result = load_pdf_tool(**args)
            
            # Get the PDF URL that Claude specified
            claude_pdf_url = args.get('pdf_url')
            
            # Add tool response - THIS IS THE KEY TEST
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })
            messages.append({
                'role': 'user',
                'content': [
                    {"type": "text", "text": "Here is the PDF file"},
                    {'type': 'file', 'file': {'file_id': claude_pdf_url}
                }]})
            
            print("Messages after tool execution:", json.dumps(messages, indent=2))
            
            # Second API call - Claude processes the PDF
            final_response = litellm.completion(
                model="anthropic/claude-sonnet-4-20250514",
                messages=messages,
                tools=[tool_schema]  # Need to include tools parameter
            )
            
            final_answer = final_response.choices[0].message.content
            print("Final response from Claude:", final_answer)
            
            # Check that we got a meaningful response
            assert final_answer is not None
            assert len(final_answer) > 10  # Should be more than just a short response
            print("✓ PDF tool response worked with actual API!")
            
        else:
            print("Claude didn't use the tool - this might be expected behavior")
            
    except Exception as e:
        print(f"API call failed: {e}")
        if "API key" in str(e) or "authentication" in str(e).lower():
            pytest.skip("Skipping actual API test - no API key available")
        else:
            raise

def test_agent_pdf_tool_claude_handling():
    """Test that our agent correctly handles PDF loading for Claude models."""
    from unittest.mock import patch, MagicMock
    from webservice.llm.agent_utils import LiteLLMChat
    
    # Mock a Claude model
    chat = LiteLLMChat("litellm/anthropic/claude-sonnet-4-20250514", tools=[])
    
    # Test that it correctly identifies as Claude model
    assert chat._is_claude_model() == True
    
    # Test a non-Claude model
    chat_gpt = LiteLLMChat("litellm/openai/gpt-4o", tools=[])
    assert chat_gpt._is_claude_model() == False
    
    # Test tool call handling for Claude with loadPdf
    class MockToolCall:
        def __init__(self):
            self.function = MagicMock()
            self.function.name = "loadPdf"
            self.function.arguments = '{"pdf_url": "https://example.com/test.pdf"}'
    
    # Mock the loadPdf function
    def mock_load_pdf(pdf_url):
        return "Ok I'm loading the PDF"
    
    chat.tool_map = {"loadPdf": mock_load_pdf}
    
    # Test _handle_tool_call for Claude model
    tool_response, user_message = chat._handle_tool_call("test_id", MockToolCall())
    
    # Verify tool response
    assert tool_response is not None
    assert tool_response["tool_call_id"] == "test_id"
    assert tool_response["role"] == "tool"
    assert tool_response["name"] == "loadPdf"
    assert tool_response["content"] == "Ok I'm loading the PDF"
    
    # Verify user message for Claude PDF handling
    assert user_message is not None
    assert user_message["role"] == "user"
    assert len(user_message["content"]) == 2
    assert user_message["content"][0]["type"] == "text"
    assert user_message["content"][0]["text"] == "Here is the PDF file"
    assert user_message["content"][1]["type"] == "file"
    assert user_message["content"][1]["file"]["file_id"] == "https://example.com/test.pdf"
    
    print("✓ Agent PDF tool handling for Claude works correctly!")


def test_agent_pdf_tool_non_claude_handling():
    """Test that our agent correctly handles PDF loading for non-Claude models."""
    from unittest.mock import MagicMock
    from webservice.llm.agent_utils import LiteLLMChat
    
    # Test a non-Claude model
    chat = LiteLLMChat("litellm/openai/gpt-4o", tools=[])
    
    # Test tool call handling for non-Claude with loadPdf
    class MockToolCall:
        def __init__(self):
            self.function = MagicMock()
            self.function.name = "loadPdf"
            self.function.arguments = '{"pdf_url": "https://example.com/test.pdf"}'
    
    # Mock the loadPdf function
    def mock_load_pdf(pdf_url):
        return "Ok I'm loading the PDF"
    
    chat.tool_map = {"loadPdf": mock_load_pdf}
    
    # Test _handle_tool_call for non-Claude model
    tool_response, user_message = chat._handle_tool_call("test_id", MockToolCall())
    
    # Verify tool response
    assert tool_response is not None
    assert tool_response["tool_call_id"] == "test_id"
    assert tool_response["role"] == "tool"
    assert tool_response["name"] == "loadPdf"
    assert tool_response["content"] == "Ok I'm loading the PDF"
    
    # Verify no user message for non-Claude models
    assert user_message is None
    
    print("✓ Agent PDF tool handling for non-Claude works correctly!")

def test_web_search_functionality():
    """Test that web search functionality works correctly with both GPT-4o and Claude models."""
    
    # Test with GPT-4o
    def test_model_web_search(model_name, model_display_name):
        print(f"\n=== Testing {model_display_name} ===")
        
        # Create LiteLLMChat with web search enabled
        sampling_params = {
            'temperature': 0.7,
            'top_p': 0.9,
            'web_search_options': {
                "search_context_size": "medium"  # Options: "low", "medium", "high"
            }
        }
        
        chat = LiteLLMChat(
            model_name=model_name,
            tools=[],  # No custom tools needed for web search
            sampling_params=sampling_params
        )
        
        # Test message asking for current information that would require web search
        messages = [
            {
                "role": "user", 
                "content": "What are the latest developments in AI safety research in 2024? Please search for recent information."
            }
        ]
        
        try:
            # Test non-streaming version
            print(f"Testing non-streaming chat with {model_display_name}...")
            response = chat.chat_with_tools(messages)
            
            # Verify we got a meaningful response
            assert response is not None
            assert len(response) > 50  # Should be a substantial response
            assert "2024" in response or "recent" in response.lower() or "latest" in response.lower()
            
            print(f"✓ Non-streaming web search worked with {model_display_name}")
            print(f"Response length: {len(response)} characters")
            print(f"Response preview: {response[:200]}...")
            
            # Test streaming version
            print(f"Testing streaming chat with {model_display_name}...")
            streaming_response_parts = []
            for event in chat.stream_chat_with_tools(messages):
                if event["type"] == "content":
                    streaming_response_parts.append(event["content"])
                elif event["type"] == "error":
                    print(f"Streaming error: {event['error']}")
                    raise Exception(f"Streaming error: {event['error']}")
            
            streaming_response = "".join(streaming_response_parts)
            
            # Verify streaming response
            assert streaming_response is not None
            assert len(streaming_response) > 50
            
            print(f"✓ Streaming web search worked with {model_display_name}")
            print(f"Streaming response length: {len(streaming_response)} characters")
            
            return True
            
        except Exception as e:
            print(f"Web search test failed for {model_display_name}: {e}")
            if "API key" in str(e) or "authentication" in str(e).lower():
                print(f"Skipping {model_display_name} test - no API key available")
                return False
            elif "rate limit" in str(e).lower() or "quota" in str(e).lower():
                print(f"Skipping {model_display_name} test - rate limit reached")
                return False
            elif "Web search options not supported" in str(e):
                print(f"Skipping {model_display_name} test - web search not supported with this model")
                return False
            else:
                raise
    
    # Test both models
    gpt4o_success = test_model_web_search("litellm/openai/gpt-4o", "GPT-4o")
    claude_success = test_model_web_search("litellm/anthropic/claude-sonnet-4-20250514", "Claude Sonnet 4")
    
    # At least one model should work for the test to pass
    if not gpt4o_success and not claude_success:
        pytest.skip("Both models failed - likely due to API key issues or rate limits")
    
    print("\n=== Web Search Test Summary ===")
    print(f"GPT-4o: {'✓ PASSED' if gpt4o_success else '✗ FAILED'}")
    print(f"Claude: {'✓ PASSED' if claude_success else '✗ FAILED'}")

def test_web_search_configuration():
    """Test that web search configuration is properly set up in LiteLLMChat."""
    
    # Test with web search options
    sampling_params_with_web_search = {
        'temperature': 0.5,
        'web_search_options': {
            "search_context_size": "high"
        }
    }
    
    chat_with_web_search = LiteLLMChat(
        model_name="litellm/openai/gpt-4o",
        tools=[],
        sampling_params=sampling_params_with_web_search
    )
    
    # Test without web search options
    sampling_params_without_web_search = {
        'temperature': 0.5
    }
    
    chat_without_web_search = LiteLLMChat(
        model_name="litellm/openai/gpt-4o",
        tools=[],
        sampling_params=sampling_params_without_web_search
    )
    
    # Verify web search options are properly stored
    assert 'web_search_options' in chat_with_web_search.sampling_params
    assert chat_with_web_search.sampling_params['web_search_options']['search_context_size'] == "high"
    
    assert 'web_search_options' not in chat_without_web_search.sampling_params
    
    print("✓ Web search configuration test passed")

def test_web_search_with_different_context_sizes():
    """Test web search with different context sizes."""
    
    context_sizes = ["low", "medium", "high"]
    
    for context_size in context_sizes:
        print(f"\n=== Testing web search with context size: {context_size} ===")
        
        sampling_params = {
            'temperature': 0.7,
            'web_search_options': {
                "search_context_size": context_size
            }
        }
        
        chat = LiteLLMChat(
            model_name="litellm/openai/gpt-4o",
            tools=[],
            sampling_params=sampling_params
        )
        
        # Verify the context size is set correctly
        assert chat.sampling_params['web_search_options']['search_context_size'] == context_size
        
        # Test with a simple query that would benefit from web search
        messages = [
            {
                "role": "user", 
                "content": "What's the current weather in New York City? Please search for this information."
            }
        ]
        
        try:
            # Test that the configuration doesn't cause errors
            params = chat._prepare_chat_params(messages)
            assert 'web_search_options' in params
            assert params['web_search_options']['search_context_size'] == context_size
            
            print(f"✓ Context size {context_size} configuration works correctly")
            
        except Exception as e:
            print(f"Configuration test failed for context size {context_size}: {e}")
            raise
    
    print("✓ All web search context sizes configured correctly")

def test_reasoning_functionality():
    """Test that reasoning functionality works correctly with Claude models."""
    
    print("\n=== Testing Claude Reasoning Functionality ===")
    
    # Create LiteLLMChat with reasoning enabled
    # Note: When reasoning is enabled, temperature must be set to 1
    sampling_params = {
        'temperature': 1.0,
        'reasoning_effort': 'high'
    }
    
    chat = LiteLLMChat(
        model_name="litellm/anthropic/claude-sonnet-4-20250514",
        tools=[],
        sampling_params=sampling_params
    )
    
    # Test message asking for reasoning/analysis
    messages = [
        {
            "role": "user", 
            "content": "Analyze the following logic puzzle step by step: If all roses are flowers, and some flowers are red, can we conclude that some roses are red? Please reason through this carefully."
        }
    ]
    
    try:
        # Test non-streaming version
        print("Testing non-streaming chat with reasoning...")
        response = chat.chat_with_tools(messages)
        
        # Verify we got a meaningful response
        assert response is not None
        assert len(response) > 100  # Should be a substantial response
        
        # Look for reasoning indicators
        reasoning_indicators = [
            "step", "analyze", "reasoning", "logic", "conclude", 
            "therefore", "because", "premise", "syllogism"
        ]
        
        response_lower = response.lower()
        reasoning_found = any(indicator in response_lower for indicator in reasoning_indicators)
        
        print(f"✓ Non-streaming reasoning worked with Claude")
        print(f"Response length: {len(response)} characters")
        print(f"Reasoning indicators found: {reasoning_found}")
        print(f"Response preview: {response[:300]}...")
        
        # Test streaming version
        print("Testing streaming chat with reasoning...")
        streaming_response_parts = []
        for event in chat.stream_chat_with_tools(messages):
            if event["type"] == "content":
                streaming_response_parts.append(event["content"])
            elif event["type"] == "error":
                print(f"Streaming error: {event['error']}")
                raise Exception(f"Streaming error: {event['error']}")
        
        streaming_response = "".join(streaming_response_parts)
        
        # Verify streaming response
        assert streaming_response is not None
        assert len(streaming_response) > 100
        
        print(f"✓ Streaming reasoning worked with Claude")
        print(f"Streaming response length: {len(streaming_response)} characters")
        
        return True
        
    except Exception as e:
        print(f"Reasoning test failed for Claude: {e}")
        if "API key" in str(e) or "authentication" in str(e).lower():
            print("Skipping reasoning test - no API key available")
            return False
        elif "rate limit" in str(e).lower() or "quota" in str(e).lower():
            print("Skipping reasoning test - rate limit reached")
            return False
        else:
            raise

def test_reasoning_configuration():
    """Test that reasoning configuration is properly set up in LiteLLMChat."""
    
    # Test with reasoning enabled
    sampling_params_with_reasoning = {
        'temperature': 0.5,
        'reasoning_effort': 'high'
    }
    
    chat_with_reasoning = LiteLLMChat(
        model_name="litellm/anthropic/claude-sonnet-4-20250514",
        tools=[],
        sampling_params=sampling_params_with_reasoning
    )
    
    # Test without reasoning
    sampling_params_without_reasoning = {
        'temperature': 0.5
    }
    
    chat_without_reasoning = LiteLLMChat(
        model_name="litellm/anthropic/claude-sonnet-4-20250514",
        tools=[],
        sampling_params=sampling_params_without_reasoning
    )
    
    # Verify reasoning options are properly stored
    assert 'reasoning_effort' in chat_with_reasoning.sampling_params
    assert chat_with_reasoning.sampling_params['reasoning_effort'] == 'high'
    
    assert 'reasoning_effort' not in chat_without_reasoning.sampling_params
    
    print("✓ Reasoning configuration test passed")
