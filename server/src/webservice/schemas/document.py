from pydantic import BaseModel
from .common import MessageResponse, ErrorResponse

# Document-related Pydantic models

class DocumentSendRequest(BaseModel):
    documentId: str | None = None
    documentPath: str | None = None

class DocumentInfoResponse(BaseModel):
    category: str
    filename: str

class DocumentSummaryResponse(BaseModel):
    summary: str

class CategoryDescriptionResponse(BaseModel):
    description: str

class DocumentPageNumberResponse(BaseModel):
    page_number: int

class DocumentFlagRequest(BaseModel):
    reason: str
    description: str | None = None

class HighlightData(BaseModel):
    page_number: int
    x: float | None = 0.1
    y: float | None = 0.1
    width: float | None = 0.8
    height: float | None = 0.1
    focus: bool | None = False

class HighlightPDFRequest(BaseModel):
    pdfUrl: str
    pageNumber: int = 1
    highlights: list[HighlightData] = []

class DownloadPdfReportRequest(BaseModel):
    sessionName: str
    htmlContent: str
    timestamp: str

# MessageResponse and ErrorResponse imported from common.py 