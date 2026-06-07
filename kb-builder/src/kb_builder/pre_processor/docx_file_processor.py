from docx import Document
from pathlib import Path
from kb_builder.pre_processor.marker_pdf import marker_blocks_using_json

def process_docx(docx_file_path: str):
    return marker_blocks_using_json(docx_file_path, 'application/msword')

    # Open the DOCX file using python-docx
    # document = Document(docx_file_path)
    
    # # Loop through each paragraph in the document
    # for paragraph in document.paragraphs:
    #     all_text += paragraph.text + "\n"  # Add a newline to separate paragraphs

    # return all_text
