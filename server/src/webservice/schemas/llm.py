from pydantic import BaseModel

# LLM-related Pydantic models

class LLMModel(BaseModel):
    id: int
    label: str
    value: str
    active: bool
    contextWindow: int
    desc: str
    excludeTraingDataPrompt: str
    useTools: bool
    useRoles: bool

class SuggestQueriesRequest(BaseModel):
    text: str

class SuggestQueriesResponse(BaseModel):
    queries: list[str]  # List of suggested queries

class SummaryRequest(BaseModel):
    text: str

class SummaryResponse(BaseModel):
    summary: str
    truncated: bool = False

class AnswerRequest(BaseModel):
    text: str
    user_query: str | None = None
    prompt_key: str | None = None
    search_query: str | None = None
    exclude_llm_knowledgebase: bool

class AnswerResponse(BaseModel):
    answer: str
    truncated: bool = False

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    repetition_penalty: float | None = None
    stop: list[str] | None = None

class ChatRequestData(BaseModel):
    chat_request: ChatRequest
    system_message: Message | None = None

class ChatResponse(BaseModel):
    role: str
    content: str 