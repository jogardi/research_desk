import os
from fastapi import HTTPException, APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse, Response, RedirectResponse, StreamingResponse
from webservice.persistence.document_sqlite import DocumentSqlite
from webservice.session_manager import protected_user_id, protected_user_kb_name
from webservice.schemas.document import (
    DocumentSendRequest, DocumentInfoResponse, HighlightPDFRequest,
    DocumentSummaryResponse, CategoryDescriptionResponse, DocumentPageNumberResponse,
    DocumentFlagRequest, DownloadPdfReportRequest
)
from webservice.schemas.common import MessageResponse
from shared.config import Config
from shared.logger import Logger

import io
import json
from pathlib import Path
import requests
import fitz  # PyMuPDF
import urllib.parse
from webservice.session_manager import protected
from typing import Iterator
from shared.kb_folders import KNOWLEDGEBASE_FOLDER

# FastAPI Router (for converted routes)
router = APIRouter(tags=["document"], dependencies=[Depends(protected)])

#
# Document routes
#

def get_document(document_id, kb_name: str) -> tuple:
    try:
        row = DocumentSqlite.get_document_filename(document_id, kb_name)
    except Exception as e:
        Logger.error("Failed to get document filename.", exception=e, report=True)
        return "Source document is not available - it was flagged!", 404
    
    if (row is None):
        return '<b style="color: red;">Source document is not available - it was flagged!<b>', 404
    
    category, filename = row
    
    return category, filename

def get_doc_page_number(category, sentence_id, kb_name: str):
    # Find the page number where the phrase appears
    page_number = DocumentSqlite.get_doc_page_number(category, sentence_id, kb_name)
    print(f"Page number: {page_number}")
    return page_number

# get souce document .pdf file route - FastAPI version
@router.get("/doc/send")
def doc_send(background_tasks: BackgroundTasks,
             documentId: str | None = None, 
             documentPath: str | None = None, 
             kb_name: str = Depends(protected_user_kb_name)):
    """
    Get source document .pdf file route - FastAPI version
    """
    print(f"+++++++++ documentId: {documentId}, documentPath: {documentPath}, kb_name: {kb_name}")
    if documentId is not None:  # if documentId is provided
        try:
            category, filename = get_document(documentId, kb_name)
        except Exception as e:
            raise HTTPException(status_code=404, detail="Document not found")
    else:  # if documentPath is provided
        if documentPath is None:
            raise HTTPException(status_code=400, detail="Either documentId or documentPath is required")
        
        document_path_parts = documentPath.split('/')
        category = '/'.join(document_path_parts[:-1])
        filename = document_path_parts[-1]

    # print(f'+++++++++ category: {category}, filename: {filename}')
    
    file_path = os.path.join(KNOWLEDGEBASE_FOLDER(kb_name), category, filename)
        
    if file_path is None or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(path=file_path, filename=filename)

# get souce document .pdf file route by filepath - FastAPI version
@router.get("/doc/send/filepath")
def doc_send_filepath(background_tasks: BackgroundTasks,
                      filepath: str, 
                      kb_name: str = Depends(protected_user_kb_name)):
    """Get source document .pdf file route by filepath."""
    file_path = os.path.join(KNOWLEDGEBASE_FOLDER(kb_name), filepath)
    
    if file_path is None or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(path=file_path, filename=os.path.basename(file_path))

# document viewer route - FastAPI version
@router.get("/doc")
def doc_viewer(documentId: str, 
               sentence_id: str | None = None,
               kb_name: str = Depends(protected_user_kb_name)):
    """Document viewer route."""
    try:
        category, filename = get_document(documentId, kb_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Document not found")

    print(f'+++++++++ category: {category}, filename: {filename}')
    page_param = ''
    if sentence_id is not None:
        page_number = get_doc_page_number(category, sentence_id, kb_name)
        # if (page_number is not None):
        #     page_param = f'#page={page_number}'
    
    encoded_sub_url = urllib.parse.quote(f"{Config.KB_FTP_KNOWLEDGEBASE_FOLDER}/{category}/{filename}{page_param}")
    print("encoded_sub_url", encoded_sub_url)
    file_url = f"{Config.DOCUMENT_SERVER_API_SERVER}/api/filemanager/download?path={encoded_sub_url}"

    print("file_url", file_url)
    
    # document_server is a 3rd party storage provider using http
    # Fetch the file from the external document server with streaming enabled
    headers = {
        'accept': '*/*',
        'authorization': 'Basic c3Q0OTAwOTp0Z0NFNEBOaA=='
    }
    
    try:
        external_response = requests.get(file_url, stream=True, verify=False, headers=headers)
        
        if external_response.status_code != 200:
            raise HTTPException(
                status_code=external_response.status_code,
                detail=f"Error fetching file, status code: {external_response.status_code}"
            )

        # Generate response stream
        def generate() -> Iterator[bytes]:
            for chunk in external_response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        print("generating response", file_url)
        
        # Return a streaming response to the client with the same content type from the external response
        return StreamingResponse(
            generate(),
            media_type=external_response.headers.get('Content-Type', 'application/octet-stream')
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document: {str(e)}")

# get souce document category and filename - FastAPI version
@router.get("/api/doc/{document_id}", response_model=DocumentInfoResponse)
def doc_info(document_id: str, kb_name: str = Depends(protected_user_kb_name)):
    """Get document category and filename by document ID."""
    try:
        row = DocumentSqlite.get_document_filename(document_id, kb_name)
    except Exception as e:
        Logger.error(f"Failed to get document filename with ID: {document_id}", exception=e, report=True)
        raise HTTPException(status_code=404, detail="Failed to get document filename - document not found.")
    
    if row is None:
        Logger.error(f"Document with ID {document_id} not found", report=True)
        raise HTTPException(status_code=404, detail="Document not found.")
    
    category, filename = row
    # check if the category has both files and folders - if so, append '/General' to the category
    try:
        categories = DocumentSqlite.getDistictCategories(kb_name)
    except Exception as e:
        Logger.error("Failed to get distinct categories from the database", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Failed to get distinct categories from the database.")
    
    if any(category_path.startswith(f'{category}/') for category_path in categories): # If the folder has both files and sub-folders
        category = category + '/General'

    return DocumentInfoResponse(category=category, filename=filename)

# get document summary - FastAPI version
@router.get("/api/doc/summary/{document_id}", response_model=DocumentSummaryResponse)
def doc_summary(document_id: str, kb_name: str = Depends(protected_user_kb_name)):
    """Get document summary by document ID."""
    try:
        summary = DocumentSqlite.get_document_summary(document_id, kb_name)
    except Exception as e:
        Logger.error(f"Failed to get document summary with ID: {document_id}", exception=e, report=True)
        raise HTTPException(status_code=404, detail="Failed to get document summary - document not found.")
    
    return DocumentSummaryResponse(summary=summary)

# get category description - FastAPI version
@router.get("/api/category/description", response_model=CategoryDescriptionResponse)
def cat_description(category: str, kb_name: str = Depends(protected_user_kb_name)):
    """Get category description."""
    try:
        description = DocumentSqlite.get_category_description(category, kb_name)
    except Exception as e:
        Logger.error(f"Failed to get category description for: {category}", exception=e, report=True)
        raise HTTPException(status_code=404, detail="Failed to get category description - category not found.")
    
    return CategoryDescriptionResponse(description=description)

# get document page number - FastAPI version
@router.post("/api/doc/pageNumber/{document_id}/{sentence_id}", response_model=DocumentPageNumberResponse)
def doc_page_number(document_id: str, sentence_id: str, kb_name: str = Depends(protected_user_kb_name)):
    """Get page number for a specific sentence in a document."""
    try:
        category, filename = get_document(document_id, kb_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Document not found")

    # Find the page number where the phrase appears
    page_number = DocumentSqlite.get_doc_page_number(category, sentence_id, kb_name)
    
    print(f"Page number: {page_number}")
    
    return DocumentPageNumberResponse(page_number=page_number)

def _get_doc_bytes_from_url(pdf_url):
    # Validate input
    if not pdf_url:
        return None, "PDF URL is required"
    
    # Decode URL if it's already encoded
    if '%' in pdf_url:
        pdf_url = urllib.parse.unquote(pdf_url)
    
    print(f"Decoded PDF URL: {pdf_url}")
    
    # Use the CORS proxy to download the PDF
    cors_proxy_url = pdf_url
    print(f"Using CORS proxy URL: {cors_proxy_url}")
    
    try:
        # Download the PDF with SSL verification disabled
        response = requests.get(
            cors_proxy_url,
            verify=False,  # Disable SSL verification
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        if response.status_code != 200:
            return None, f"Failed to download PDF: HTTP {response.status_code}"
        
        print(f"Successfully downloaded PDF, size: {len(response.content)} bytes")
        
        # Load the PDF with PyMuPDF
        pdf_data = io.BytesIO(response.content)
        return pdf_data, None
    except requests.RequestException as e:
        return None, f"Request error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def _get_doc_bytes_from_file(file_path, kb_name: str):
    file_path = os.path.join(KNOWLEDGEBASE_FOLDER(kb_name), file_path)
    print(f"*** file_path: {file_path}")
    try:
        with open(file_path, 'rb') as file:
            data = io.BytesIO(file.read())
        return data, None
    except Exception as e:
        Logger.error(f"Failed to read file: {str(e)}", exception=e, report=True)
        return None, f"Failed to read file: {str(e)}"

def _remove_duplicate_highlights(highlights):
    """Remove duplicate highlights based on position coordinates and prioritize focus highlights"""
    # Sort highlights first so focus=True highlights come later and "win" over duplicates
    sorted_highlights = sorted(highlights, key=lambda h: h.get('focus', False))
    
    unique_dict = {}  # Use dict to allow overwriting duplicates
    
    for highlight in sorted_highlights:
        region_key = (
            highlight.get('page_number'),
            highlight.get('x', 0.1),
            highlight.get('y', 0.1), 
            highlight.get('width', 0.8),
            highlight.get('height', 0.1)
        )
        # This will overwrite any previous highlight at the same position
        # So focus=True highlights will overwrite focus=False ones
        if region_key in unique_dict:
            print(f"DEBUG: Overwriting duplicate at {region_key}")
        unique_dict[region_key] = highlight
    
    return list(unique_dict.values())

@router.post("/api/doc/highlight-pdf")
def highlight_pdf(request: HighlightPDFRequest, kb_name: str = Depends(protected_user_kb_name)):
    """
    Highlight a PDF document with the provided highlights and return the modified PDF.
    """
    try:
        # Extract parameters from request model
        pdf_url = request.pdfUrl
        page_number = request.pageNumber
        highlights = [highlight.dict() for highlight in request.highlights]
        
        print(f"Received request to highlight PDF: {pdf_url}, page: {page_number}, highlights: {highlights}")
        
        # pdf_data, error = _get_doc_bytes_from_url(pdf_url) 
        pdf_data, error = _get_doc_bytes_from_file(pdf_url, kb_name)

        if error:
            raise HTTPException(status_code=400, detail=error)
        
        # Check if any highlight has None positioning values
        has_invalid_positioning = False
        for highlight in request.highlights:
            if (highlight.x is None or highlight.y is None or 
                highlight.width is None or highlight.height is None):
                has_invalid_positioning = True
                break
        # if any highlight has None positioning values, return the original PDF content
        if has_invalid_positioning:
            Logger.warning(f"Invalid positioning values detected, returning original PDF content for file: {pdf_url}")
            return Response(
                content=pdf_data.getvalue(),
                media_type='application/pdf',
                headers={'Content-Disposition': 'attachment; filename="highlighted.pdf"'}
            )
        
         # all positioning values are valid Proceed with highlighting only
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        
        # Check if page number is valid
        if page_number < 1 or page_number > len(doc):
            raise HTTPException(status_code=400, detail=f"Invalid page number: {page_number}")
        
        # Remove duplicate highlights before processing
        unique_highlights = _remove_duplicate_highlights(highlights)

        for highlight in unique_highlights:
            # Get the page (PyMuPDF uses 0-based indexing)
            page_number = highlight.get('page_number') - 1
            page = doc[page_number]
            
            # Get page dimensions
            page_rect = page.rect
            cropbox = page.cropbox
            
            # Default highlight values if not provided
            highlight_x = highlight.get('x', 0.1)
            highlight_y = highlight.get('y', 0.1)
            highlight_width = highlight.get('width', 0.8)
            highlight_height = highlight.get('height', 0.1)
        
            # Calculate highlight rectangle (convert from relative to absolute coordinates)
            x = highlight_x * cropbox.x1
            y = highlight_y * cropbox.y1
            # x += page.cropbox.x0 * page.cropbox.width / page.mediabox.width
            # y += page.cropbox.y0 * page.cropbox.height / page.mediabox.height
            width = highlight_width * cropbox.x1
            height = highlight_height * cropbox.y1
            
            # Create highlight rectangle
            highlight_rect = fitz.Rect(x, y, x + width, y + height)
            
            # Add highlight (yellow with some transparency)
            annot = page.add_highlight_annot(highlight_rect)
            # annot.set_colors(stroke=(1, 0.8, 0))
            light_blue = (0.75, 0.85, 1)
            light_yellow = (0.85, 1.0, 0.85)
            
            focus_value = highlight.get('focus')
            color = light_blue if focus_value else light_yellow
            
            annot.set_colors(stroke=color)
            annot.update()
        
        # print(f"Added highlight at: x={x}, y={y}, width={width}, height={height}")
        
        # Save the modified PDF
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        # Return the modified PDF using FastAPI Response
        return Response(
            content=output.getvalue(),
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename="highlighted.pdf"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error highlighting PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# flag document - FastAPI version
@router.put("/api/doc/flag/{document_id}", response_model=MessageResponse)
def doc_flag(document_id: str, request: DocumentFlagRequest, user_id: str = Depends(protected_user_id), kb_name: str = Depends(protected_user_kb_name)):
    """Flag a document."""
    try:
        DocumentSqlite.flag_document(user_id, document_id, request.reason, request.description, kb_name) 
    except Exception as e:
        Logger.error("Failed to flag document.", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Failed to flag document.")

    return MessageResponse(message="Document has been flagged.")

# unflag document - FastAPI version
@router.put("/api/doc/unflag/{document_id}", response_model=MessageResponse)
def doc_unflag(document_id: str, kb_name: str = Depends(protected_user_kb_name)):
    """Unflag a document."""
    try:
        DocumentSqlite.unflag_document(document_id, kb_name) 
    except Exception as e:
        Logger.error("Failed to unflag document.", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Failed to unflag document.")

    return MessageResponse(message="Document has been unflagged.")

@router.post("/api/reports/download-pdf-report")
def download_pdf_report(request: DownloadPdfReportRequest):
    """Generate and download a PDF report from HTML content."""
    # replace <b> with <b class="keyword">:
    request.htmlContent = request.htmlContent.replace('<b>', '<b class="keyword">')

    try:
        # Import weasyprint for HTML to PDF conversion
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # Clean the session name to make it a valid filename
        import re
        from datetime import datetime

        clean_filename = re.sub(r'[^\w\s-]', '', request.sessionName)
        clean_filename = re.sub(r'[-\s]+', '-', clean_filename)
        filename = f"{clean_filename}.pdf"
        
        # Format timestamp to user-friendly format
        try:
            # Parse ISO timestamp
            dt = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
            # Format as "January 15, 2025 at 3:45 PM"
            formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            # Fallback to original timestamp if parsing fails
            formatted_date = request.timestamp

        # Create basic CSS for better PDF formatting
        css_content = """
        @page {
            size: A4;
            margin: 0.75in;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
        }
        .h1-title {
            text-align: center;
            padding-bottom: 0px;
            margin-bottom: 0px;
        }
        .h1-subtitle {
            text-align: center;
            margin-top: 0px;
            margin-bottom: 10px;
            font-size: 16px;
            font-weight: bold;
            opacity: 0.7;
        }

        /* Override inline width constraints to use full available width */
        div[style*="width: 75%"] {
            width: 100% !important;
            max-width: 100% !important;
        }
        .p-mx-auto {
            width: 100% !important;
            max-width: 100% !important;
        }
        .subtitle {
            font-size: 16px;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .text-h5 {
            font-size: 20px;
            font-weight: bold;
        }
        .text-subtitle1 {
            font-size: 13px;
            font-weight: bold;
        }
        .text-subtitle2 {
            font-size: 12px;
            font-weight: bold;
        }
        .text-bold {
            font-weight: bold;
        }
        .hilite-sentence {
            color: #0d47a1;
            padding: 2px;
        }
        .keyword {
            color: #a1887f;
            padding: 2px;
        }
        .message-content {
            margin-left: 20px;
            margin-bottom: 10px;
        }
        .chunk-text {
            margin-bottom: 15px;
            border-bottom: 1px solid #ccc;
            padding-bottom: 10px;
        }
        hr {
            border: 0;
            border-top: 1px solid #ccc;
            margin: 10px 0;
        }
        a {
            color: #0066cc;
            text-decoration: none;
        }
        p {
            margin: 8px 0;
        }
        /* Table styling */
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
            font-size: 12px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            vertical-align: top;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        /* PDF Bookmarks for sidebar navigation - only main sections */
        #summary {
            bookmark-level: 1;
            bookmark-label: "Summary";
        }
        #insights {
            bookmark-level: 1;
            bookmark-label: "Insights";
        }
        #concepts {
            bookmark-level: 1;
            bookmark-label: "Concepts";
        }
        #chats {
            bookmark-level: 1;
            bookmark-label: "Chats";
        }
        #context-docs {
            bookmark-level: 1;
            bookmark-label: "Context";
        }
        /* Prevent subsections from becoming bookmarks */
        h1, h2, h3, h4, h5, h6 {
            bookmark-level: none;
        }
        """
        

        
        # Create complete HTML document with title
        html_document = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{request.sessionName}</title>
        </head>
        <body>
            <h1 class="h1-title">{request.sessionName}</h1>
            <h1 class="h1-subtitle">Thought Flow Report</h1>
            <div style="font-size: 10px; text-align: center; color: #666; margin-bottom: 20px;">
                Generated on: {formatted_date}
            </div>
            {request.htmlContent}
        </body>
        </html>
        """
        
        # Convert HTML to PDF
        font_config = FontConfiguration()
        html_obj = HTML(string=html_document)
        css_obj = CSS(string=css_content, font_config=font_config)
        
        # Generate PDF in memory
        pdf_buffer = io.BytesIO()
        html_obj.write_pdf(pdf_buffer, stylesheets=[css_obj], font_config=font_config)
        pdf_buffer.seek(0)
        
        # Return PDF as file response
        return Response(
            content=pdf_buffer.getvalue(),
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/pdf'
            }
        )
        
    except ImportError:
        raise HTTPException(
            status_code=500, 
            detail="PDF generation library not available. Please install weasyprint."
        )
    except Exception as e:
        Logger.error("Failed to generate PDF report.", exception=e, report=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")
