import os
import re
import json

from webservice.llm.agent import LiteLLMChat
from webservice.llm import agent
os.environ["HF_HUB_DISABLE_TQDM"] = "1"
from huggingface_hub.utils import are_progress_bars_disabled, disable_progress_bars, enable_progress_bars
disable_progress_bars()

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List
from shared.config import Config
from webservice.hparams_config import hpc
from shared.logger import Logger
from webservice.llm.together.summary_chat import generate_summary
from webservice.llm.together.answer_chat import generate_answer
from webservice.llm.together.suggest_queries_chat import generate_queries
from webservice.llm.together.together_chat_completion import TogetherChatCompletion
from webservice.llm.openai.openai_chat_completion import OpenAIChatCompletion
from webservice.llm.llm_types import ChatRequest
from webservice.persistence.user_mgmt_backendless import UserMgmtBackendless
from shared.call_llm_api import retry_generate_until_success
from webservice.schemas.llm import (
    LLMModel, SuggestQueriesRequest, SummaryRequest, SummaryResponse,
    AnswerRequest, AnswerResponse, ChatRequestData, ChatResponse
)
from webservice.session_manager import protected

router = APIRouter(tags=["llm"], dependencies=[Depends(protected)])

def _truncate_text_for_context_limit(error_message, text):
    """
    Calculate a safe truncation length based on context length error message.
    
    Args:
        error_message: The error message containing context length information
        text: The original text that caused the error
        
    Returns:
        tuple: (truncated_text, max_length) if successful, (None, None) if failed
    """
    # Extract the maximum context length from the error message
    max_length_match = re.search(r"maximum context length is (\d+)", error_message)
    max_length = int(max_length_match.group(1)) if max_length_match else 0
    
    if max_length <= 0:
        return None, None
        
    # Extract token counts from error message
    tokens_match = re.search(r"requested (\d+) tokens \((\d+) in the messages, (\d+) in the completion\)", error_message)
    if not tokens_match:
        return None, None
        
    total_tokens = int(tokens_match.group(1)) # total tokens in the request
    message_tokens = int(tokens_match.group(2)) # tokens in the messages
    completion_tokens = int(tokens_match.group(3)) # tokens in the completion
    
    # Calculate safe token limit (90% of max to leave room for the model)
    safe_limit = int(max_length * 0.9) - completion_tokens
    
    # Estimate characters per token (rough approximation)
    chars_per_token = len(text) / message_tokens if message_tokens > 0 else 4
    
    # Calculate safe character limit
    safe_char_limit = int(safe_limit * chars_per_token)
    
    # Truncate text
    truncated_text = text[:safe_char_limit]
    Logger.info(f"Truncating text from {len(text)} chars to {len(truncated_text)} chars")
    
    return truncated_text, max_length

#
# LLM routes
# 
@router.post("/api/llm/summary", response_model=SummaryResponse)
def summarize(request: SummaryRequest):
    """Generate a summary of the provided text."""
    try:
        summary, error_response = generate_summary(request.text)
    except Exception as e:
        Logger.error("Failed to generate summary", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Failed to generate summary")

    if error_response is not None:
        error_data = error_response.json().get('error', {}) 
        if error_data.get('type', '') == "invalid_request_error" and "longer than the model's context length" in error_data.get('message', ''):
            Logger.error(f"Text exceeds maximum context window length", response=error_response, report=True)
            raise HTTPException(status_code=422, detail=f"Maximum context window length exceeded for summary generation")

        Logger.error("Failed to generate summary", response=error_response, report=True)
        raise HTTPException(status_code=error_response.status_code, detail="Failed to generate summary")
      
    return SummaryResponse(summary=summary)

@router.post("/api/llm/answer", response_model=AnswerResponse)
def answer(request: AnswerRequest):
    """Generate an answer based on the provided text and query."""
    Logger.info(f"Prompt key: {request.prompt_key}")
    Logger.info(f"Search query: {request.search_query}")

    prompts = { "INSIGHTS": hpc().PROMPT_INSIGHTS, "CONCEPTS": hpc().PROMPT_CONCEPTS, "QUESTIONS": hpc().PROMPT_QUESTIONS, "SEARCH_QUERIES": hpc().PROMPT_SEARCH_QUERIES }
    
    # Determine the actual user query based on prompt_key
    if request.prompt_key is not None:
        user_query = prompts[request.prompt_key]
        if request.search_query is not None:
            user_query = user_query.replace("<search_query>", request.search_query)
    else:
        user_query = request.user_query

    try:
        answer_text, error_response = generate_answer(user_query, request.text, request.exclude_llm_knowledgebase)
    except Exception as e:
        Logger.error("Failed to generate answer", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Failed to generate answer")

    if error_response is not None:
        error_data = error_response.json().get('error', {}) 
        if error_data.get('type', '') == "invalid_request_error" and "longer than the model's context length" in error_data.get('message', ''):
            Logger.error(f"Text exceeds maximum context window length", response=error_response, report=True)
            raise HTTPException(status_code=422, detail="Maximum context window length exceeded for answer generation")
            
        Logger.error("Failed to generate answer", response=error_response, report=True)
        raise HTTPException(status_code=error_response.status_code, detail="Failed to generate answer")
    
    return AnswerResponse(answer=answer_text)

@router.post("/api/llm/suggest_queries", response_model=List[str])
def suggest_queries(request: SuggestQueriesRequest):
    """Generate suggested queries based on the provided text."""
    try:
        queries, error_response = generate_queries(request.text)
    except Exception as e:
        Logger.error("Failed to generate suggested queries", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Failed to generate suggested queries")

    if error_response is not None:
        error_data = error_response.json().get('error', {}) 
        if error_data.get('type', '') == "invalid_request_error" and "longer than the model's context length" in error_data.get('message', ''):
            Logger.error(f"Text exceeds maximum context window length", response=error_response, report=True)
            raise HTTPException(status_code=422, detail="Maximum context window length exceeded for suggested query generation")
            
        Logger.error("Failed to generate suggested queries", response=error_response, report=True)
        raise HTTPException(status_code=error_response.status_code, detail="Failed to generate suggested queries")
    
    # Convert the queries to a JSON array
    queries_list = queries.split("|")
    return queries_list

@router.post("/api/llm/chat", response_model=ChatResponse)
def chat(request: ChatRequestData):
    """Generate a chat response based on the provided chat request."""
    if request.chat_request.model.startswith("gemini"):
        import google.generativeai as genai
        genai.configure()
        if request.system_message:
            model = genai.GenerativeModel(request.chat_request.model, system_instruction=request.system_message.content)
        else:
            model = genai.GenerativeModel(request.chat_request.model)
        print("sent")
        print("start query")
        assistant_message = { 
            "role": "assistant", 
            "content": retry_generate_until_success(model, request.chat_request.messages[0].content).strip()
        }
        print("finish query")
        print("got response")
    else:
        # Convert to dict only when needed for the LLM functions
        chat_request = request.chat_request.dict()
        if request.system_message:
            chat_request['messages'].insert(0, request.system_message.dict()) # Add the system message to the beginning of the messages list
        try: 
            if (request.chat_request.model == "gpt-4o"):
                assistant_message, error_response = OpenAIChatCompletion.query(chat_request)
            else:
                assistant_message, error_response = TogetherChatCompletion.query(chat_request)
        except Exception as e:
            Logger.error("Failed to generate chat response", exception=e, report=True)
            raise HTTPException(status_code=500, detail="Failed to generate chat response")

        if error_response is not None:
            Logger.error("Failed to generate chat response", response=error_response, report=True)
            raise HTTPException(status_code=500, detail="Failed to generate chat response")
    
    return ChatResponse(role=assistant_message["role"], content=assistant_message["content"])

@router.post("/api/llm/stream_chat")
def stream_chat(request: ChatRequestData):
    """Streams text response with semantic search capability"""
    request_dict = request.dict()
    gen_stream = agent.stream_chat(request_dict)
    return StreamingResponse(gen_stream, media_type='text/event-stream')

@router.get("/api/llm/models", response_model=List[LLMModel])
def get_models():
    """Get the list of supported LLM models and the default model.""" 
    from webservice.models import models # Temporary until moved to database table
    
    return models

