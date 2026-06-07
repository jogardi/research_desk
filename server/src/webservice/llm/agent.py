from shared.config import cfg, Config
import json
from webservice.llm.agent_prompts import get_gemini_consultation_prompt, get_fast_then_slow_enhancement_prompt
from webservice.llm.agent_utils import LiteLLMChat
from webservice.llm.prepare_prompts import document_to_text_with_page_numbers
from webservice.llm.llm_types import ChatRequest
from webservice.excerpts.db_operations import store_excerpt, generate_excerpt_hash
from shared.pdf_parse_helper import load_pdf_page_as_image
from shared.logger import Logger


# Global variable to track total pixels from all images
TOTAL_IMAGE_PIXELS = 0

def consultGemini(question: str, context: str = '') -> str:
    """Consult Gemini 2.5 Pro for advice, second opinions, or alternative ideas on a specific question or topic

    Parameters
    ----------
    question : str
        The specific question or topic you want advice on
    context : str, optional
        Optional context or background information to help Gemini provide more relevant advice

    Returns
    -------
    str
        Gemini's advice and insights
    """
    import litellm
    
    # Prepare the prompt for Gemini
    prompt = get_gemini_consultation_prompt(question, context)
    
    try:
        # Call Gemini 2.5 Pro directly
        response = litellm.completion(
            model="gemini/gemini-2.5-pro",
            messages=[
                {"role": "user", "content": prompt}
            ],
            reasoning_effort="high"
        )
        
        advice = response.choices[0].message.content
        return f"Gemini 2.5 Pro's advice:\n\n{advice}"
        
    except Exception as e:
        Logger.error(f"Error consulting Gemini: {str(e)}", report=True)
        return f"Error consulting Gemini: {str(e)}"

def _prepare_messages_tools_and_llm(payload, emit, model_name, kb_name: str):
    """Prepare the initial messages, build tools, and create LiteLLMChat instance.
    
    Parameters
    ----------
    payload : dict
        The payload containing chat_request and optional system_message
    emit : callable
        The emit function for socket communication
    model_name : str
        The name of the model being used
        
    Returns
    -------
    tuple
        (messages, llm) - List of messages and configured LiteLLMChat instance
    """
    chat_request: ChatRequest = payload['chat_request']
    messages = chat_request['messages'].copy()
    
    # Add system message if provided
    if 'system_message' in payload:
        messages.insert(0, payload['system_message'])
        print(f"Added system message: {payload['system_message']}")
    
    # Build tools list
    agent = SocketAgent(emit, chat_request, kb_name)
    tools = []
    
    # Get use_tools configuration - if null, don't use any tools
    use_tools = payload.get('use_tools')
    
    if use_tools is not None:
        # Add tools based on the use_tools configuration
        if use_tools.get('searchSemanticByDoc', False):
            tools.append(agent.searchSemanticByDoc)
        
        if use_tools.get('readPage', False):
            tools.append(agent.readPage)
        
        # Add loadPdf tool only for Claude models and if enabled
        is_claude_model = 'anthropic' in model_name.lower() or 'claude' in model_name.lower()
        if use_tools.get('loadPdf', False) and is_claude_model:
            tools.append(agent.loadPdf)
    
    # Create sampling parameters
    sampling_params = {
        'temperature': chat_request.get('temperature'),
        'top_p': chat_request.get('top_p'),
    }
    if payload.get('enable_web_search'):
        sampling_params['web_search_options'] = {
            "search_context_size": "high"  # Options: "low", "medium", "high"
        }
    if payload.get('enable_reasoning'):
        sampling_params['reasoning_effort'] = "high"

    from webservice.llm.model_sampling_params import apply_model_sampling_params
    apply_model_sampling_params(model_name, sampling_params, payload)
    
    # Create LiteLLMChat instance
    llm = LiteLLMChat(model_name, tools=tools, sampling_params=sampling_params)
    
    return messages, llm

def _stream_llm_response(llm, messages, emit=lambda x, y: None):
    """Stream responses from LLM with tool support.
    
    Parameters
    ----------
    llm : LiteLLMChat
        The LLM chat instance
    messages : list
        List of messages to send to the LLM
    emit : callable
        Function to emit socket events
        
    Yields
    ------
    str
        Content chunks from the LLM response
    """
    try:
        for event in llm.stream_chat_with_tools(messages=messages):
            if event["type"] == "content":
                yield event["content"]
            elif event["type"] == "error":
                Logger.error(f"Error: {event['error']}", report=True)
                print(f"Error: {event['error']}")
                emit('error', event['error'])
    except Exception as e:
        print(f"Error in _stream_llm_response: {str(e)}")
        Logger.error(f"Error in _stream_llm_response: {str(e)}", report=True)
        error_message = f"**Processing Error:** {str(e)}\n\nPlease try rephrasing your question or try again later."
        emit('error', error_message)

def _run_gemini_in_background(messages, chat_request):
    """Run Gemini 2.5 Pro in a background thread and return the response dict.
    
    Parameters
    ----------
    messages : list
        List of messages to send to Gemini
    chat_request : dict
        The chat request containing temperature and top_p settings
        
    Returns
    -------
    dict
        Dictionary that will be populated with response content, error, and completion status
    """
    import threading
    
    # Storage for Gemini's response
    gemini_response = {"content": None, "error": None, "completed": False}
    
    def run_gemini():
        """Run Gemini 2.5 Pro in a separate thread and store the response."""
        try:
            # Create a new LiteLLMChat instance for Gemini
            gemini_sampling_params = {
                'temperature': chat_request['temperature'],
                'top_p': chat_request['top_p'],
                'reasoning_effort': "high"
            }
            gemini_chat = LiteLLMChat(
                "litellm/gemini/gemini-2.5-pro",
                tools=None,  # No tools for the background Gemini call
                sampling_params=gemini_sampling_params
            )
            
            # Get the full response from Gemini (non-streaming)
            response = gemini_chat.chat_with_tools(messages)
            gemini_response["content"] = response
            print("response from gemini:", response)
            
        except Exception as e:
            gemini_response["error"] = str(e)
            Logger.error(f"Error running Gemini: {str(e)}", report=True)
            print(f"Error running Gemini: {str(e)}")
        finally:
            gemini_response["completed"] = True
    
    # Start Gemini in a background thread
    gemini_thread = threading.Thread(target=run_gemini)
    gemini_thread.start()
    
    return gemini_response, gemini_thread

class SocketAgent:

    def __init__(self, emit, chat_request, kb_name: str):
        self.emit = emit
        self.chat_request = chat_request
        self.kb_name = kb_name

    def searchSemanticByDoc(self, user_query: str) -> str:
        """Search through the user's documents semantically based on user query

        Parameters
        ----------
        user_query : str
            The search query to find relevant documents

        Returns
        -------
        str
            Search results formatted with excerpt hashes that can be cited using square brackets (e.g., [a1b2])
        """
        print("searchSemanticByDoc", user_query)
        from webservice.search.semantic_search import searchSemanticByDoc as search_func
        self.emit('query', user_query)
        documents, error_msg, status_code = search_func(
            categories=self.chat_request['categories'],
            user_query=user_query,
            kb_name=self.kb_name,
            top_k=100
        )
        if error_msg is None and documents:
            result_text = "SEARCH RESULTS:\n\n"
            
            for idx, doc in enumerate(documents, 1):
                result_text += document_to_text_with_page_numbers(doc, self.kb_name) + "\n\n"
            print("===================================")
            print("got result text:", result_text)
            print("===================================")
            
            return result_text
        else:
            Logger.error(f"Failed to search documents: {error_msg}", report=True)
            raise Exception("Failed to search documents", error_msg)

    def readPage(self, page_number: int, document_path: str) -> list:
        """Retrieve the page as an image so that you can see the text, tables and figures.
        
        IMPORTANT: Use the exact document_path from search results. Do not guess or make up paths.
        Construct the document path from the search results by concatenating the Category and the Document: "Category/Document". 
        For example: 
        Category: Example Category
        Document: sample-document.pdf
        Document path: Example Category/sample-document.pdf

        Parameters
        ----------
        page_number : int
            The page number to retrieve the text from
        document_path : str
            The document path from search results. Must match the path information shown in search results exactly.
            Format: "Category/Document" (e.g., "Example Category/sample-document.pdf")

        Returns
        -------
        list
            Content array with text and image_url components
        """
        print(f"Reading page {page_number} from document {document_path}")
        self.emit('read_page', json.dumps({'document_path': document_path, 'page_number': page_number}))
        from shared.kb_folders import KNOWLEDGEBASE_FOLDER
        pdf_path = f'{KNOWLEDGEBASE_FOLDER(self.kb_name)}/{document_path}'
        img = load_pdf_page_as_image(pdf_path, page_number)
        
        # Track image pixels
        global TOTAL_IMAGE_PIXELS
        try:
            from PIL import Image
            import io
            import base64
            
            # Extract image data from the data URL
            if img.startswith('data:image'):
                # Remove the data URL prefix to get the base64 data
                base64_data = img.split(',')[1]
                image_data = base64.b64decode(base64_data)
                
                # Open the image to get dimensions
                with Image.open(io.BytesIO(image_data)) as pil_img:
                    width, height = pil_img.size
                    pixels = width * height
                    TOTAL_IMAGE_PIXELS += pixels
                    print(f"Image dimensions: {width}x{height} = {pixels:,} pixels")
                    print(f"Total pixels processed so far: {TOTAL_IMAGE_PIXELS:,}")
        except Exception as e:
            Logger.error(f"Warning: Could not calculate image pixels: {e}", report=True)
            print(f"Warning: Could not calculate image pixels: {e}")
        
        return [
            {
                "type": "text",
                "text": "Here is the image."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": img
                }
            }
        ]

    def loadPdf(self, pdf_url: str) -> str:
        """Load a PDF from the specified URL and return it for analysis

        Parameters
        ----------
        pdf_url : str
            URL of the PDF to load

        Returns
        -------
        str
            Simple confirmation message (the actual PDF will be added by special handling for Claude)
        """
        print(f"Loading PDF from URL: {pdf_url}")
        
        # Validate the URL
        if not pdf_url or not pdf_url.startswith('http'):
            Logger.error(f"Error: Invalid PDF URL provided. Please provide a valid HTTP URL. {pdf_url}", report=True)
            return "Error: Invalid PDF URL provided. Please provide a valid HTTP URL."
        
        
        # Check if URL ends with .pdf or has a proper filename
        if not pdf_url.endswith('.pdf') and '/pdf/' in pdf_url:
            Logger.error(f"Error: Incomplete PDF URL. Please provide the full URL including the PDF filename. {pdf_url}", report=True)
            return "Error: Incomplete PDF URL. Please provide the full URL including the PDF filename."
        
        self.emit('load_pdf', json.dumps({'pdf_url': pdf_url}))
        
        return "Ok I'm loading the PDF"

    

def stream_chat(payload, kb_name: str, emit=lambda x, y: None):
    # payload has the key 'use_tools'. If it is null, then we don't use 
    # if it is not null then it is a Dict[str, bool] with keys searchSemanticByDoc, readPage, loadPdf indicating weather those tools are enabled
    
    # Extract and store citation metadata if provided
    citation_metadata = payload.get('citation_metadata', {})
    if citation_metadata:
        for hash_id, excerpt_info in citation_metadata.items():
            # Store each excerpt in the database
            try:
                store_excerpt(
                    document_id=excerpt_info['documentID'],
                    chunk_ids=excerpt_info['chunkIds'],
                    kb_name=kb_name,
                    excerpt_hash=hash_id
                )
                print(f"Stored excerpt {hash_id} for document {excerpt_info['documentID']}")
            except Exception as e:
                Logger.error(f"Error storing excerpt {hash_id}: {str(e)}", report=True)
                print(f"Error storing excerpt {hash_id}: {str(e)}")
    
    chat_request: ChatRequest = payload['chat_request']

    model_name = chat_request['model']
    
    # Check if this is the fast-then-slow model
    if model_name == 'litellm/fast-then-slow':
        return stream_fast_then_slow_chat(payload, kb_name, emit)
    
    print(f"Initial messages: {json.dumps(chat_request['messages'], indent=2)}")
    assert model_name.startswith('litellm')

    # Prepare messages, tools, and LLM instance
    messages, llm = _prepare_messages_tools_and_llm(payload, emit, model_name, kb_name)
    
    # Use the new streaming helper
    return _stream_llm_response(llm, messages, emit)

def stream_fast_then_slow_chat(payload, kb_name: str, emit=lambda x, y: None):
    """Handle the fast-then-slow hybrid model that combines GPT-4o and Gemini 2.5 Pro."""
    chat_request: ChatRequest = payload['chat_request']
    
    # Prepare messages, tools, and LLM instance for GPT-4o
    # Note: We always include loadPdf for the fast-then-slow model for consistency
    gpt4o_model_name = "litellm/openai/gpt-4o"
    messages, gpt4o_chat = _prepare_messages_tools_and_llm(payload, emit, gpt4o_model_name, kb_name)
    
    # Start Gemini in background
    gemini_response, gemini_thread = _run_gemini_in_background(messages, chat_request)
    
    # Stream GPT-4o's initial response
    gpt4o_response_parts = []
    for chunk in _stream_llm_response(gpt4o_chat, messages, emit):
        gpt4o_response_parts.append(chunk)
        yield chunk
    
    # Wait for Gemini to complete (with timeout)
    gemini_thread.join(timeout=30)  # 30 second timeout
    
    if gemini_response["completed"] and gemini_response["content"] and not gemini_response["error"]:
        # Prepare enhancement prompt for GPT-4o
        yield "\n\n---\n\n"  # Visual separator
        
        enhancement_messages = messages.copy()
        enhancement_messages.append({
            "role": "assistant",
            "content": "".join(gpt4o_response_parts)
        })
        enhancement_messages.append({
            "role": "system",
            "content": get_fast_then_slow_enhancement_prompt(gemini_response["content"])
        })
        
        # Stream GPT-4o's enhancement
        yield "**Additional insights after consulting Gemini 2.5 Pro:**\n\n"
        
        # Use the streaming helper for enhancement too
        for chunk in _stream_llm_response(gpt4o_chat, enhancement_messages, emit):
            yield chunk
