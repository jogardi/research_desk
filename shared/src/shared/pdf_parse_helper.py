import pdfplumber
import io
from PIL import Image
import base64
from shared.hparams_config import hpc

def load_pdf_page_as_image(pdf_path: str, page_number: int, bbox=None, page_bbox=None) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        assert page_number > 0
        page = pdf.pages[page_number - 1]
        page_image = page.to_image(resolution=hpc().PDF_RESOLUTION)
        
        # If bbox is provided, crop the image to the specified region
        if bbox:
            # Get original page dimensions 
            page_width = page_bbox[2]
            page_height = page_bbox[3]
            
            # Convert relative bbox coordinates to pixel coordinates based on rendered image
            x0, y0, x1, y1 = bbox
            # Access width and height from the original PIL image
            img_width, img_height = page_image.original.width, page_image.original.height
            
            x0_px = int((x0 / page_width) * img_width)
            y0_px = int((y0 / page_height) * img_height)
            x1_px = int((x1 / page_width) * img_width)
            y1_px = int((y1 / page_height) * img_height)
            
            # Crop the image
            pil_image = page_image.original
            cropped_image = pil_image.crop((x0_px, y0_px, x1_px, y1_px))
            
            # Save cropped image to buffer
            img_buffer = io.BytesIO()
            cropped_image.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            # open('/tmp/img.png', 'wb').write(img_buffer.getvalue())
        else:
            # Save full page image to buffer
            img_buffer = io.BytesIO()
            page_image.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            # print("saving full page image from", pdf_path, page_number)
            # open('/tmp/img2.png', 'wb').write(img_buffer.getvalue())
            
        return f'data:image/png;base64,{base64.b64encode(img_buffer.getvalue()).decode("utf-8")}'