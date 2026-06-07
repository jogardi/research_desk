import json
import litellm
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generator, List, Optional, Union, get_type_hints
from shared.utils import dict2obj, truncate_dict_strings
import dotenv
dotenv.load_dotenv()

class LiteLLMChat:
    """A wrapper for LiteLLM that provides chat functionality with optional tool calling."""
    
    def __init__(self, model_name: str, tools: Optional[List[Union[Callable, Dict[str, Any]]]] = None,
                 sampling_params: Optional[Dict[str, Any]] = None):
        """Initialize the LiteLLM chat wrapper.

        Args:
            model_name: The full model name (e.g., 'litellm/openai/gpt-4')
            tools: List of functions or tool dictionaries. Functions should have proper docstrings.
            sampling_params: Dictionary of sampling parameters (e.g., {'temperature': 0.7, 'top_p': 0.9})
        """
        self.model = '/'.join(model_name.split('/')[1:])  # Remove 'litellm' prefix
        self.tools = tools or []
        self.tool_map = {}
        self.tool_schemas = []
        
        # Automatically determine if the model supports function calling
        self.enable_tools = litellm.supports_function_calling(self.model)
        
        # Process tools - convert functions to schemas and build tool map
        for tool in self.tools:
            if callable(tool):
                raw_schema = litellm.utils.function_to_dict(tool)
                # Wrap in OpenAI function calling format
                schema = {
                    "type": "function",
                    "function": raw_schema
                }
                
                self.tool_schemas.append(schema)
                self.tool_map[schema['function']['name']] = tool
            elif isinstance(tool, dict):
                # It's already a schema dictionary
                self.tool_schemas.append(tool)
                # For dict tools, we can't map back to a function easily
                # This is for backward compatibility if needed
            else:
                raise ValueError(f"Tool must be a callable function or dict, got {type(tool)}")
        
        # Store sampling parameters, filtering out None values
        self.sampling_params = {k: v for k, v in (sampling_params or {}).items() if v is not None}

    def _is_claude_model(self) -> bool:
        """Check if the current model is a Claude/Anthropic model."""
        return 'anthropic' in self.model.lower() or 'claude' in self.model.lower()

    def _prepare_chat_params(
        self,
        messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Prepare parameters for the LLM API call."""
        params = {
            "model": self.model,
            "messages": messages,
        }
        if self.enable_tools and self.tool_schemas:
            params["tools"] = self.tool_schemas
            params["tool_choice"] = "auto"
        
        # Add sampling parameters if set
        params.update(self.sampling_params)
            
        return params

    def _handle_tool_call(
        self,
        tool_call_id: str,
        tool_call: Any,
    ) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Process a single tool call and return the tool response if successful.
        
        Returns:
            tuple of (tool_response, optional_user_message)
            The optional_user_message is used for Claude PDF handling
        """
        print("tool call", tool_call)
        try:
            args = json.loads(tool_call.function.arguments)
            
            tool_func = self.tool_map.get(tool_call.function.name)
            if tool_func is None:
                raise ValueError(f"Tool function '{tool_call.function.name}' not found")
            
            # Call the function with the arguments
            result = tool_func(**args)
            
            if result is None:
                raise ValueError("Tool function returned None")
            
            # Check if this is a loadPdf call on a Claude model
            if tool_call.function.name == 'loadPdf':
                # For Claude PDF loading, we need special handling
                # The result should be a list with text and potentially other content
                pdf_url = args.get('pdf_url')
                if pdf_url.startswith('http://'):
                    pdf_url = pdf_url.replace('http://', 'https://', 1)
                    print(f"Converted HTTP to HTTPS: {pdf_url}")
                
                # Tool response with minimal info
                tool_response = {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": result if isinstance(result, str) else json.dumps(result)
                }
                
                # User message with the actual PDF file
                user_message = {
                    'role': 'user',
                    'content': [
                        {"type": "text", "text": "Here is the PDF file"},
                        {'type': 'file', 'file': {'file_id': pdf_url}}
                    ]
                }
                
                return tool_response, user_message
            else:
                # Normal tool handling
                tool_response = {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": result
                }
                return tool_response, None
        except json.JSONDecodeError as e:
            print(f"Failed to parse tool arguments: {str(e)}")
            raise
        except Exception as e:
            print(f"Tool execution failed: {str(e)}")
            raise

    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
    ) -> str:
        """Non-streaming version of chat conversation with optional function/tool calling."""
        working_messages = messages.copy()

        while True:
            params = self._prepare_chat_params(
                working_messages,
            )
            params['stream'] = False
            # print("sending messages", truncate_dict_strings(params))
            response = litellm.completion_with_retries(**params)
            assistant_message = response.choices[0].message
            working_messages.append(assistant_message)
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                print("tool calls", response.choices[0].message)
                tool_calls = response.choices[0].message.tool_calls
                
                for tool_call in tool_calls:
                    tool_response, user_message = self._handle_tool_call(tool_call.id, tool_call)
                    working_messages.append(tool_response)
                    # Add user message if it exists (for Claude PDF handling)
                    if user_message:
                        working_messages.append(user_message)
            else:
                return assistant_message["content"]

    def stream_chat_with_tools(
        self,
        messages: List[Dict[str, str]],
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream a chat conversation with optional function/tool calling capabilities."""
        working_messages = messages.copy()
        active_tool_calls: Dict[str, Dict[str, Any]] = {}
        not_done = True
        debug_f = open('/tmp/chat_record.txt', 'a')
        def write_msg(msg):
            content = msg['content']
            if isinstance(content, list):
                # Handle list content (e.g., for Claude PDF messages)
                content_str = str(content)
            else:
                content_str = str(content)
            debug_f.write('\n\n' + content_str)
        
        while not_done:
            not_done = False
            params = self._prepare_chat_params(
                working_messages,
            )
            params['stream'] = True
            try:
                response_stream = litellm.completion_with_retries(**params)
            except Exception as e:
                print(f'litellm error: {e}')
                if ('The file format is invalid or unsupported' in e.message 
                    and len(working_messages) >= 2 
                    and working_messages[-1]['role'] == 'user' 
                    and 'file' in working_messages[-1]['content'][1]
                    and working_messages[-2]['role'] == 'tool'
                    ):
                    print("recovering")
                    
                    tool_response = working_messages[-2]
                    tool_response['content'] = 'Sorry I can\'t get this file. Maybe it\'s not a valid pdf.'
                    # remove the last message
                    working_messages.pop()
                    not_done = True
                    continue
                else:
                    raise e

            assistant_message = None
            cur_tool_id = None

            for chunk in response_stream:
                # Handle tool calls
                if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.tool_calls:
                    tool_calls = chunk.choices[0].delta.tool_calls
                    assert len(tool_calls) == 1
                    for tool_call in tool_calls:
                        if tool_call.id is not None:
                            cur_tool_id = tool_call.id
                        if cur_tool_id not in active_tool_calls:
                            tc = tool_call
                            active_tool_calls[tool_call.id] = {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments or ""
                                }
                            }

                            if assistant_message is None:
                                assistant_message = {
                                    "role": "assistant",
                                    "tool_calls": []
                                }
                                working_messages.append(assistant_message)
                            assistant_message["tool_calls"].append(active_tool_calls[tool_call.id])
                        else:
                            # Continuing existing tool call
                            active_call = active_tool_calls[cur_tool_id]
                            active_call["function"]["arguments"] += tool_call.function.arguments or ""
                # Handle tool call completion
                elif chunk.choices[0].finish_reason == "tool_calls":
                    print("finish with tool call", chunk.choices[0])
                    for tool_call_id, tool_call in active_tool_calls.items():
                        print("tool call", tool_call)
                        tool_response, user_message = self._handle_tool_call(tool_call_id, dict2obj(tool_call))
                        working_messages.append(tool_response)
                        write_msg(tool_response)
                        # Add user message if it exists (for Claude PDF handling)
                        if user_message:
                            working_messages.append(user_message)
                            write_msg(user_message)
                        not_done = True

                    active_tool_calls.clear()
                    break
                # Handle regular content
                elif hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.content:
                    yield {
                        "type": "content",
                        "content": chunk.choices[0].delta.content
                    }
                elif hasattr(chunk.choices[0], 'delta'):
                    if chunk.choices[0].finish_reason != 'stop':
                        print('unknown delta: ', chunk)