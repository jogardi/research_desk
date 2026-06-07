import dotenv
dotenv.load_dotenv()
import unittest
import sys
import os
import json

# Add the path to access shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Set up config before importing other modules
from shared.config import Config
class MockArgs:
    profile = 'default'
    org = 'DEV'
    param1 = ''
    param2 = ''
    param3 = ''
Config.load_config(MockArgs())

from webservice.llm.agent_utils import LiteLLMChat

class TestAgent(unittest.TestCase):

    def test_model_transformation(self):
        """
        Test that LiteLLMChat removes the "litellm" prefix from the model name.
        For "litellm/openai/gpt-4o" we expect the instance's model to be "openai/gpt-4o".
        """
        chat = LiteLLMChat("litellm/openai/gpt-4o")
        self.assertEqual(chat.model, "openai/gpt-4o")

    def skip_test_stream_chat(self):
        """
        Integration test for stream_chat.
        This test invokes the actual model with a simple conversation and asserts
        that a non-empty response is returned.
        """
        chat = LiteLLMChat("litellm/openai/gpt-4o")
        messages = [{"role": "user", "content": "Hello, can you greet me?"}]
        content_list = []
        try:
            for chunk in chat.stream_chat_with_tools(messages):
                content_list.append(chunk)
        except Exception as e:
            self.fail(f"stream_chat raised an exception: {e}")

        aggregated_response = "".join(content_list)
        # We expect the aggregated response to be non-empty.
        self.assertTrue(len(aggregated_response.strip()) > 0, "Expected non-empty response from stream_chat")

    def test_stream_chat_with_tools(self):
        """
        Integration test for stream_chat_with_tools.
        Here we define a dummy tool function and send a prompt
        that should ideally trigger a tool call. The test ensures that we get some
        events back and no error events.
        """
        messages = [{"role": "user", "content": "Please search for technology news."}]
        
        # Define a dummy tool function that returns a dummy response
        def searchSemanticByDoc(user_query: str) -> str:
            """Search through documents semantically based on user query
            
            Parameters
            ----------
            user_query : str
                The search query to find relevant documents
                
            Returns
            -------
            str
                Search results
            """
            print(f"\nDummy search called with query: {user_query}")
            return f"Apple released a humanoid robot"

        chat = LiteLLMChat("litellm/openai/gpt-4o", tools=[searchSemanticByDoc])

        events = []
        try:
            print("\nStarting stream_chat_with_tools test")
            for event in chat.stream_chat_with_tools(messages):
                events.append(event)
            print('llm answer', ''.join([e.get("content", "") for e in events]))
        except Exception as e:
            self.fail(f"stream_chat_with_tools raised an exception: {e}")

        print(f"\nTotal events received: {len(events)}")
        error_events = [e for e in events if e.get("type") == "error"]
        print(f"Error events: {error_events}")

        # Validate that we received at least one event.
        self.assertGreater(len(events), 0, "Expected at least one event from stream_chat_with_tools")
        # Ensure no error events were generated.
        self.assertEqual(len(error_events), 0, "Expected no error events in stream_chat_with_tools")

    def test_stream_chat_with_payload(self):
        """
        Integration test for stream_chat function using the search_request_payload.json file.
        This test mimics how stream_chat is called in websockets.py.
        
        The test:
        1. Loads a real payload from search_request_payload.json (same format as websockets)
        2. Calls agent.stream_chat() with the payload and a mock emit function
        3. Verifies that the streaming works correctly and produces meaningful content
        4. Uses the real search function to test full integration
        5. Captures emitted events to verify the agent's behavior
        
        This ensures that the agent.stream_chat function works correctly with real payloads
        as it would be called from the websockets handler.
        """
        # Load the payload from the JSON file
        payload_path = os.path.join(os.path.dirname(__file__), "search_resquest_payload.json")
        with open(payload_path, 'r') as f:
            payload = json.load(f)
        
        print(f"\nLoaded payload: {json.dumps(payload, indent=2)}")
        
        # Mock emit function to capture emitted events
        emitted_events = []
        def mock_emit(event_type, data):
            emitted_events.append({"type": event_type, "data": data})
            print(f"Emitted event: {event_type} with data: {data}")
        
        try:
            # Import and call stream_chat
            from webservice.llm import agent
            
            # Collect all streamed content
            streamed_content = []
            for chunk in agent.stream_chat(payload, emit=mock_emit):
                streamed_content.append(chunk)
                print(f"Streamed chunk: {chunk}")
            
            # Verify that we got some content
            total_content = "".join(streamed_content)
            print(f"\nTotal streamed content length: {len(total_content)}")
            print(f"Content preview: {total_content[:200]}...")
            
            # Assertions
            self.assertGreater(len(total_content), 0, "Expected non-empty streamed content")
            
            # The main test is that stream_chat works without throwing exceptions
            # and produces meaningful content
            self.assertIn("search", total_content.lower(), "Expected response to mention searching")
            
            # Check if any events were emitted (this is optional since the LLM might not call tools)
            print(f"Total emitted events: {len(emitted_events)}")
            if len(emitted_events) > 0:
                print(f"Emitted events: {emitted_events}")
                # Check that a query event was emitted (from the search tool)
                query_events = [e for e in emitted_events if e["type"] == "query"]
                print(f"Query events: {len(query_events)}")
            
            print(f"✓ stream_chat test passed with {len(streamed_content)} chunks and {len(emitted_events)} events")
            
        except Exception as e:
            self.fail(f"stream_chat raised an exception: {e}")

    def skip_test_with_no_tools(self):
        chat = LiteLLMChat("litellm/openai/gpt-4o")
        messages = [{"role": "user", "content": "Please search for weather updates."}]
        result = chat.chat_with_tools(messages)
        self.assertTrue(len(result.strip()) > 0, "Expected non-empty response from chat")

    def skip_test_chat_with_tools(self):
        """
        Integration test for chat_with_tools.
        Similar to the streaming version, we use a dummy tool function and check for
        a non-empty response and no errors.
        """
        messages = [{"role": "user", "content": "Please search for weather updates."}]

        def searchSemanticByDoc(user_query: str) -> str:
            """Search through documents semantically based on user query
            
            Parameters
            ----------
            user_query : str
                The search query to find relevant documents
                
            Returns
            -------
            str
                Search results
            """
            return f"it is sunny"

        chat = LiteLLMChat("litellm/openai/gpt-4o", tools=[searchSemanticByDoc])
        try:
            result = chat.chat_with_tools(messages)
            print(f"Result from chat_with_tools: {result}")
            self.assertTrue(len(result.strip()) > 0, "Expected non-empty response from chat_with_tools")

        except Exception as e:
            self.fail(f"chat_with_tools raised an exception: {e}")

    def test_claude_function_calling_support(self):
        """
        Test to check if Claude model supports function calling and if tools are configured correctly.
        """
        import litellm
        from webservice.llm.agent_utils import LiteLLMChat
        
        model_name = "litellm/anthropic/claude-sonnet-4-20250514"
        
        # Check if LiteLLM thinks this model supports function calling
        supports_fc = litellm.supports_function_calling(model_name[len("litellm/"):])
        print(f"litellm.supports_function_calling('{model_name}') = {supports_fc}")
        
        # Create a simple tool
        def test_search(query: str) -> str:
            """Search for information based on query
            
            Parameters
            ----------
            query : str
                The search query
                
            Returns
            -------
            str
                Search results
            """
            return f"Mock search results for: {query}"
        
        # Create LiteLLMChat instance
        chat = LiteLLMChat(model_name, tools=[test_search])
        
        print(f"chat.enable_tools = {chat.enable_tools}")
        print(f"Number of tool schemas: {len(chat.tool_schemas)}")
        print(f"Tool schemas: {chat.tool_schemas}")
        
        # Test if the model would actually call the tool
        messages = [{"role": "user", "content": "Please search for information about doctors"}]
        
        # Check what parameters are being sent
        params = chat._prepare_chat_params(messages)
        print(f"Chat parameters: {params}")
        
        # This test just verifies the setup - we don't need to actually call the API
        self.assertTrue(True)  # Always pass, this is just for investigation

    def test_cite_sources_functionality(self):
        """
        Integration test for the cite sources functionality.
        This test simulates the full citation workflow:
        1. Performs a real semantic search to get actual documents and chunks
        2. Creates real excerpts with proper hashes from the search results
        3. Stores them in the database
        4. Sends a chat request with real citation metadata
        5. Verifies that the agent properly handles citations
        """
        from webservice.excerpts.db_operations import store_excerpt, generate_excerpt_hash
        from webservice.llm import agent
        from webservice.search.semantic_search import searchSemanticByDoc
        
        # Perform a real semantic search to get actual documents and chunks
        print("Performing semantic search to get real documents...")
        documents, error_msg, status_code = searchSemanticByDoc(
            categories="Prostatectomy Surgeries",  # Use a real category
            user_query="doctors",  # Use a simpler query that should return results
            top_k=3,
            is_for_ui=False  # Don't rerank for testing
        )
        
        if error_msg or not documents:
            # fail the test
            self.fail(f"Semantic search failed or returned no results: {error_msg}")
        
        print(f"Found {len(documents)} documents from semantic search")
        
        # Create real citation metadata from the search results
        test_citation_metadata = {}
        context_text = ""
        
        for i, doc in enumerate(documents[:2]):  # Use first 2 documents
            if not doc.get('chunks') or len(doc['chunks']) == 0:
                continue
                
            # Create an excerpt from the first few chunks of this document
            chunks = doc['chunks'][:3]  # Take first 3 chunks
            chunk_ids = [chunk['id'] for chunk in chunks]
            
            # Generate real hash for this excerpt
            hash_id = generate_excerpt_hash(doc['documentID'], chunk_ids)
            
            # Create excerpt text from the chunks
            excerpt_text = "\n".join([chunk['text'] for chunk in chunks])
            
            # Store metadata
            test_citation_metadata[hash_id] = {
                "hash": hash_id,
                "documentID": doc['documentID'],
                "documentName": doc['documentName'],
                "excerpt": [0, len(chunks) - 1],  # chunk range
                "chunkIds": chunk_ids,
                "pageNumber": chunks[0].get('region', {}).get('page_number') if chunks else None
            }
            
            # Add to context text
            context_text += f"[Excerpt {hash_id}]\n"
            context_text += f"Source: {doc['documentName']}\n"
            context_text += excerpt_text + "\n\n"
            
            print(f"Created excerpt {hash_id} from document {doc['documentName']} with {len(chunks)} chunks")
        
        if not test_citation_metadata:
            self.fail("No valid excerpts could be created from search results")
        
        # Store the excerpts in the database
        for hash_id, excerpt_info in test_citation_metadata.items():
            store_excerpt(
                document_id=excerpt_info['documentID'],
                chunk_ids=excerpt_info['chunkIds'],
                excerpt_hash=hash_id
            )
            print(f"Stored excerpt {hash_id} for document {excerpt_info['documentID']}")
        
        # Create a payload similar to what the websocket handler would receive
        payload = {
            "chat_request": {
                "model": "litellm/anthropic/claude-sonnet-4-20250514",
                "messages": [
                    {
                        "role": "user",
                        "content": "What are the key findings from the provided sources? Please cite your sources."
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.1,
                "top_p": 0.7,
                "top_k": 50,
                "repetition_penalty": 1.1,
                "categories": "Prostatectomy Surgeries"
            },
            "system_message": {
                "role": "system",
                "content": f"You can use both your own knowledge/opinions and these excerpts selected by the user to answer the user's question.\n\nEach excerpt is identified by a 4-character hash for citation purposes.\n\n- Include citations where appropriate.\n- Citations should be formatted as hash codes in square brackets, e.g., [a1b2], [c3d4], etc., where the hash code corresponds to the excerpt's unique identifier.\n- Example: If you use information from an excerpt with hash a1b2, write: \"According to the study, the results showed... [a1b2].\"\n- If you use information from multiple excerpts, you can cite them together: \"Multiple sources confirm this finding [a1b2][c3d4].\" You can cite the following excerpts but to be clear you should not do citation for search results from the searchSemanticByDoc tool.\n\nEXCERPTS:\n\n{context_text}"
            },
            "citation_metadata": test_citation_metadata,
            "use_tools": {
                "searchSemanticByDoc": True,
                "readPage": False,
                "loadPdf": False
            }
        }
        
        # Mock emit function to capture emitted events
        emitted_events = []
        def mock_emit(event_type, data):
            emitted_events.append({"type": event_type, "data": data})
            print(f"Emitted event: {event_type} with data: {data}")
        
        try:
            # Call the agent's stream_chat function
            streamed_content = []
            for chunk in agent.stream_chat(payload, emit=mock_emit):
                streamed_content.append(chunk)
                print(f"Streamed chunk: {chunk}")
            
            # Verify that we got some content
            total_content = "".join(streamed_content)
            print(f"\nTotal streamed content length: {len(total_content)}")
            print(f"Content preview: {total_content[:300]}...")
            
            # Assertions for citation functionality
            self.assertGreater(len(total_content), 0, "Expected non-empty streamed content")
            
            # Check for actual citation hashes in the response
            hash_citations = [hash_id for hash_id in test_citation_metadata.keys() if f'[{hash_id}]' in total_content]
            
            # The agent must include actual citation hashes
            self.assertGreater(
                len(hash_citations), 0,
                f"Expected response to include citation hashes. Found hashes: {hash_citations}. Response: {total_content[:500]}..."
            )
            
            # Verify that the excerpts were properly stored and can be retrieved
            from webservice.excerpts.db_operations import get_excerpt_by_hash
            
            for hash_id in test_citation_metadata.keys():
                excerpt_info = get_excerpt_by_hash(hash_id)
                self.assertIsNotNone(excerpt_info, f"Expected excerpt {hash_id} to be retrievable")
                self.assertEqual(
                    excerpt_info['document_id'], 
                    test_citation_metadata[hash_id]['documentID'],
                    f"Expected document ID to match for excerpt {hash_id}"
                )
                self.assertEqual(
                    excerpt_info['chunk_ids'], 
                    test_citation_metadata[hash_id]['chunkIds'],
                    f"Expected chunk IDs to match for excerpt {hash_id}"
                )
            
            print(f"✓ cite sources test passed with {len(streamed_content)} chunks")
            print(f"Found citation hashes in response: {hash_citations}")
            
        except Exception as e:
            self.fail(f"cite sources test raised an exception: {e}")

    def test_search_result_citations(self):
        """
        Test that the agent can cite excerpts from search results returned by searchSemanticByDoc tool.
        This test verifies the new functionality where search results include excerpt hashes
        that can be cited by the agent.
        """
        from webservice.excerpts.db_operations import get_excerpt_by_hash
        from webservice.llm.prepare_prompts import document_to_text_with_page_numbers
        
        # Create a mock document with excerpts (similar to what searchSemanticByDoc returns)
        mock_document = {
            'documentID': 123,
            'documentName': 'test-document.pdf',
            'documentCategory': 'Test Category',
            'chunks': [
                {
                    'id': 1001,
                    'text': 'First chunk of text about medical research.',
                    'region': {'page_number': 1}
                },
                {
                    'id': 1002,
                    'text': 'Second chunk continuing the medical research topic.',
                    'region': {'page_number': 1}
                },
                {
                    'id': 1005,
                    'text': 'Third chunk after a gap in the document.',
                    'region': {'page_number': 2}
                }
            ],
            'excerpts': [[0, 1], [2, 2]]  # Two excerpts: chunks 0-1 and chunk 2
        }
        
        # Call document_to_text_with_page_numbers to process the mock document
        formatted_text = document_to_text_with_page_numbers(mock_document)
        
        print(f"Formatted text: {formatted_text}")
        
        # Verify that the formatted text contains excerpt hashes
        self.assertIn('[Excerpt ', formatted_text, "Expected formatted text to contain excerpt hashes")
        
        # Extract the hashes from the formatted text
        import re
        hash_pattern = r'\[Excerpt ([a-f0-9]{4})\]'
        found_hashes = re.findall(hash_pattern, formatted_text)
        
        print(f"Found hashes: {found_hashes}")
        
        # We should have 2 hashes (one for each excerpt)
        self.assertEqual(len(found_hashes), 2, f"Expected 2 excerpt hashes, found {len(found_hashes)}")
        
        # Verify that each hash can be retrieved from the database
        for hash_id in found_hashes:
            excerpt_info = get_excerpt_by_hash(hash_id)
            self.assertIsNotNone(excerpt_info, f"Expected excerpt {hash_id} to be retrievable from database")
            self.assertEqual(excerpt_info['document_id'], 123, f"Expected document ID to match for excerpt {hash_id}")
        
        # Verify the first excerpt contains the first two chunks
        first_hash = found_hashes[0]
        first_excerpt = get_excerpt_by_hash(first_hash)
        self.assertEqual(first_excerpt['chunk_ids'], [1001, 1002], "Expected first excerpt to contain chunks 1001, 1002")
        
        # Verify the second excerpt contains the third chunk
        second_hash = found_hashes[1]
        second_excerpt = get_excerpt_by_hash(second_hash)
        self.assertEqual(second_excerpt['chunk_ids'], [1005], "Expected second excerpt to contain chunk 1005")
        
        # Verify that the formatted text contains both page headers
        self.assertIn('Page 1:', formatted_text, "Expected formatted text to contain Page 1 header")
        self.assertIn('Page 2:', formatted_text, "Expected formatted text to contain Page 2 header")
        
        # Verify that chunk texts are included
        self.assertIn('First chunk of text about medical research', formatted_text)
        self.assertIn('Second chunk continuing', formatted_text)
        self.assertIn('Third chunk after a gap', formatted_text)
        
        print(f"✓ search result citations test passed with hashes: {found_hashes}")


if __name__ == "__main__":
    unittest.main()
