import argparse
import pdfplumber
from PIL import Image
import google.generativeai as genai
import io
import pickle

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="Path to the PDF file to process")
    args = parser.parse_args()

    # 1) Configure your API key for Google Generative AI (Gemini)
    #    If you've set an environment variable, you can skip this.
    genai.configure()

    # 2) Create an instance of the Gemini model
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    # 3) Prompt to be used for each page
    prompt = (
        "Translate this image of a page of a PDF to markdown. The markdown supports LaTeX. "
        "Represent tables you see as JSON. Translate figures to JSON or mermaid, whichever is easier for you."
    )
    
    pdf_path = args.pdf_path
    
    # List to accumulate responses
    responses = []

    # 5) Convert each PDF page to an image and call Gemini
    for pil_img, page_idx in pdf_to_images(pdf_path, resolution=200):
        print(f"Processing page {page_idx + 1}...")
        
        # The snippet from your example: model.generate_content([prompt, image])
        # We provide [prompt, pil_img] as the argument array
        response = model.generate_content([prompt, pil_img])
        
        # Append the raw response (or a specific field if you prefer) to our list
        responses.append(response)
    
    # 6) Save the responses to a pickle file for later usage
    with open("responses.pkl", "wb") as f:
        pickle.dump(responses, f)
    
    print("Done! Responses saved to 'responses.pkl'.")

if __name__ == "__main__":
    main()
