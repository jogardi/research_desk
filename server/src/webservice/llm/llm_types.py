from typing import Dict, Any, TypedDict, Optional

class Message(TypedDict):
    role: str
    content: str

class ChatRequest(TypedDict, total=False):
    model: str
    messages: list[Message]
    max_tokens: int
    temperature: float
    top_p: float
    top_k: int
    repetition_penalty: float
    stop: Optional[list[str]]

class PromptRequest(TypedDict, total=False):
    model: str
    prompt: str
    max_tokens: int
    temperature: float
    top_p: float
    top_k: int
    repetition_penalty: float
    stop: Optional[list[str]]

