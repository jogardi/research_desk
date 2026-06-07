import dotenv
from kb_builder.load_env import load_env
load_env(override=True)
import pdfplumber
from pathlib import Path
from shared.config import Config
from kb_builder.hparams_config import hpc
from kb_builder.pre_processor.pdf_block import PDFBlock, PdfRegion
from shared.logger import Logger
import pdfplumber
from PIL import Image
import google.generativeai as genai
import io
from typing import List
from concurrent.futures import ThreadPoolExecutor
from shared.cache import mem
 
def pdfplumber_process_pdf(pdf_file_path: str) -> List[PDFBlock]:
    blocks = []

    # Open the PDF file using pdfplumber
    with pdfplumber.open(pdf_file_path) as pdf:
        # Loop through each page in the PDF
        for page in pdf.pages:
            # Extract text from the page and add it to the all_text string
            text = page.extract_text(layout=True)
            if text:  # Ensure there is text on the page before adding it
                for part in text.split('\n\n'):
                    blocks.append(PDFBlock(text=part, type="Text", region=PdfRegion(page_number=page.page_number)))

    return blocks

def pdf_page_as_image(pdf_path: str, page_number: int, resolution=200):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]
        page_image = page.to_image(resolution=resolution)
        img_buffer = io.BytesIO()
        page_image.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return Image.open(img_buffer)

def pdf_to_images(pdf_path, resolution=200):
    """
    Yields each PDF page as a PIL Image.
    :param pdf_path: Path to your PDF file.
    :param resolution: DPI for rendering pages to images (higher = bigger image).
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            # Convert page to an in-memory image
            page_image = page.to_image(resolution=resolution)
            
            # Save image to a BytesIO buffer
            img_buffer = io.BytesIO()
            page_image.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            
            # Open the image buffer with PIL
            pil_img = Image.open(img_buffer)
            yield pil_img, page_index

def gemini_process_pdf(pdf_path: str):
    # 1) Configure your API key for Google Generative AI (Gemini)
    #    If you've set an environment variable, you can skip this.
    genai.configure()

    # 2) Create an instance of the Gemini model
    print('model', hpc().gemini_pdf.model[len('litellm/gemini/'):])
    model = genai.GenerativeModel(hpc().gemini_pdf.model[len('litellm/gemini/'):],
                                  generation_config={"max_output_tokens": 32000})
    
    # 3) Get prompt from config
    prompt = hpc().gemini_pdf.prompt
    
    # List to accumulate responses
    responses = []

    # 4) Convert each PDF page to an image and call Gemini
    for pil_img, page_idx in pdf_to_images(pdf_path, resolution=200):
        
        # The snippet from your example: model.generate_content([prompt, image])
        # We provide [prompt, pil_img] as the argument array
        response = model.generate_content([prompt, pil_img])
        
        # Append the raw response (or a specific field if you prefer) to our list
        responses.append(response.text)
    
    return responses

def process_single_page(args):
    from litellm import completion
    import base64
    
    pil_img, page_idx, prompt, model_name = args
    
    # Convert image to base64 string
    img_buffer = io.BytesIO()
    pil_img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    image_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

    messages = [
        {
            "role": "user", 
            "content": [
                { 'type': 'text', 'text': prompt },
                { 
                    'type': 'image_url',
                    'image_url': {'url': "data:image/png;base64,{}".format(image_data) }
                }
            ]
        }
    ]

    response = completion(
        model=model_name[len('litellm/'):],
        messages=messages,
        max_tokens=8192
    )

    content = response.choices[0].message.content
    assert content
    return PDFBlock(text=content, type="Text", region=PdfRegion(page_number=page_idx))

@mem()
def litellm_process_pdf(pdf_path: str):
    # Retrieve the prompt and model name from configuration
    prompt = hpc().litellm_pdf.prompt
    model_name = hpc().litellm_pdf.model

    # Convert PDF to list of (image, index) tuples first
    page_data = list(pdf_to_images(pdf_path, resolution=200))
    
    # Prepare arguments for each worker
    worker_args = [(img, idx, prompt, model_name) for img, idx in page_data]
    
    # Process pages in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=16) as executor:
        responses = list(executor.map(process_single_page, worker_args))
    
    return responses

def pymupdf_process_pdf(pdf_file_path: str) -> str:
    import pymupdf
    doc = pymupdf.open(pdf_file_path)
    all_text = [
        page.get_text() for page in doc
    ]
    doc.close()
    return all_text

def plumb_and_chunk(pdf_file_path: str) -> List[PDFBlock]:
    Logger.info("using pdfplumber")
    blocks = pdfplumber_process_pdf(pdf_file_path)
    if hpc().enable_agentic_chunking:
        from kb_builder.pre_processor.agentic_chunk_only import agentic_chunk_only
        print(f"Applying agentic chunking only (no correction)")
        blocks = agentic_chunk_only(blocks)
    return blocks


def process_pdf(pdf_file_path: str) -> List[PDFBlock]: 
    default_pdf_processor = hpc().DEFAULT_PDF_PROCESSOR
    print("default_pdf_processor", default_pdf_processor)
    if default_pdf_processor == "gemini":
        try:
            return gemini_process_pdf(pdf_file_path)
        except Exception as err:
            Logger.warning(f"Error processing PDF with Gemini: {pdf_file_path} {err}")
            return pdfplumber_process_pdf(pdf_file_path)
    elif default_pdf_processor == "pymupdf":
        return pymupdf_process_pdf(pdf_file_path)
    elif default_pdf_processor == "litellm":
        return litellm_process_pdf(pdf_file_path)
    elif default_pdf_processor == "marker":
        from kb_builder.pre_processor.marker_pdf import marker_process_pdf
        return marker_process_pdf(pdf_file_path)
    elif default_pdf_processor == "marker_json":
        from kb_builder.pre_processor.marker_pdf import marker_blocks_using_json 
        try:
            blocks = marker_blocks_using_json(pdf_file_path)
        except Exception as err:
            Logger.warning(f"Error processing PDF with marker_json: {pdf_file_path} {err}")
            return plumb_and_chunk(pdf_file_path)

        # Apply either agentic chunking or post-correction if enabled
        if hpc().enable_agentic_chunking:
            from kb_builder.pre_processor.agentic_chunk_correct import agentic_chunk_correct
            print(f"Applying agentic chunking and correction")
            out_blocks = agentic_chunk_correct(pdf_file_path, blocks)
            assert len(out_blocks) == len(blocks), f"Number of blocks changed from {len(blocks)} to {len(out_blocks)}"
            blocks = out_blocks
        elif hpc().enable_post_correction:
            from kb_builder.pre_processor.post_correct import post_correct
            print(f"Applying post-correction with strategy: {hpc().post_correct_strategy}")
            blocks = post_correct(pdf_file_path, blocks, strategy=hpc().post_correct_strategy)
        
        return blocks
    else:
        return plumb_and_chunk(pdf_file_path)

