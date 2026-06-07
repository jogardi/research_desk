# I want to use llm to correct the transcription of the pdf
import dotenv
from kb_builder.load_env import load_env
load_env(override=True)
from litellm import completion_with_retries
from tqdm import tqdm
from pydantic import BaseModel
from typing import List, Iterable
from kb_builder.pre_processor.marker_pdf import PDFBlock
from kb_builder.hparams_config import hpc
import pdfplumber
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

def pdf_to_images(pdf_path, resolution=164) -> Iterable[bytes]:
    """
    Yields each PDF page as a PIL Image.
    :param pdf_path: Path to your PDF file.
    :param resolution: DPI for rendering pages to images (higher = bigger image).
    """
    import io
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            # Convert page to an in-memory image
            page_image = page.to_image(resolution=resolution)
            
            # Save image to a BytesIO buffer
            img_buffer = io.BytesIO()
            page_image.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            # # print width and height
            # from PIL import Image
            # image = Image.open(img_buffer)
            # print('page image width and height', image.width, image.height)
            
            yield img_buffer

class Fix(BaseModel):
    line_number: int
    replacement: str

class FixResult(BaseModel):
    fixes: list[Fix]

def group_blocks_by_page(blocks: List[PDFBlock]) -> dict:
    """
    Groups the PDFBlock objects by their page number.
    """
    from collections import defaultdict
    blocks_by_page = defaultdict(list)
    for block in blocks:
        page_num = block.region.page_number
        if page_num is not None:
            blocks_by_page[page_num].append(block)
    return blocks_by_page

def get_page_images_as_base64(pdf_file_path: str, page_numbers: set) -> dict:
    """
    Converts pages (that have PDFBlocks) to base64-encoded PNG images.
    """
    import base64
    images = {}
    for page_num, img_buffer in enumerate(pdf_to_images(pdf_file_path), start=1):
        if page_num in page_numbers:
            img_b64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
            images[page_num] = img_b64
    return images

def generate_prompt_text(block: PDFBlock) -> str:
    """
    Generates the prompt that instructs the LLM to correct transcription errors.
    """
    prompt_text = (
        "Please correct any transcription errors in the following text block extracted from the PDF. "
        "The block text is provided along with the PDF page image. Return your corrections as a JSON "
        "object with a key 'fixes' that is a list of objects. Each object must include the 'line_number' "
        "(starting at 1) and the corrected 'replacement' for that specific line.\n\n"
        "<block>\n" + block.text + "\n</block>"
    )
    return prompt_text

def apply_fixes_to_text(text: str, fixes: List[dict] | None) -> str:
    """
    Apply the fixes provided by the LLM to the original text.
    """
    if not fixes:
        return text
    lines = text.split("\n")
    for fix in fixes:
        idx = fix["line_number"]
        replacement = fix["replacement"]
        if replacement is not None and 0 <= idx < len(lines):
            # print("original line", lines[idx])
            # print("replacement", replacement)
            lines[idx] = replacement
    return "\n".join(lines)

def generate_prompt_text_for_page(blocks: List[PDFBlock]) -> tuple[str, list[tuple[int, int]]]:
    """
    Generates a prompt for an entire page by combining all blocks.
    Each block is wrapped in <block> tags and every line is prefixed with a global line number.
    Returns a tuple of:
      - the complete prompt text
      - a list of tuples (start_line, num_lines) for each block indicating
        the global line number where the block began and its number of lines.
    """
    prompt = (
        "Please correct any transcription errors in the following text blocks extracted from the PDF page. "
        "Assign corrections using global line numbers (starting at 1 for the page). "
        "IMPORTANT RULES:\n"
        "1. Only provide fixes for lines that actually have errors\n"
        "2. Each line number should appear at most ONCE in your fixes\n"
        "3. Do not repeat the same fix multiple times\n"
        "4. Keep your response concise\n"
        "Return your corrections as a JSON object with a key 'fixes' that is a list of objects. "
        "Each object must include the 'line_number' and the corrected 'replacement' for that specific line.\n\n"
    )
    block_line_offsets = []  # List of (start_line, num_lines) for each block.
    global_line = 1
    for block in blocks:
        prompt += "<block>\n"
        lines = block.text.split("\n")
        num_lines = len(lines)
        block_line_offsets.append((global_line, num_lines))
        for line in lines:
            prompt += f"{global_line} {line}\n"
            global_line += 1
        prompt += "</block>\n"
    return prompt, block_line_offsets

def correct_page(blocks: List[PDFBlock], img_b64: str, cache=False) -> List[PDFBlock]:
    """
    Corrects all blocks on a page in one LLM call.
    The prompt is generated to include all blocks with global line numbers.
    After receiving fixes, the fixes are re-grouped (and adjusted) per block,
    then applied using the standard apply_fixes_to_text function.
    """
    prompt_text, block_line_offsets = generate_prompt_text_for_page(blocks)
    model_name = hpc().post_correct_llm[len('litellm/'):]
    is_together = model_name.startswith('together_ai')


    cache_args = {}
    if cache:
        cache_args = {
            "cache_control": {"type": "ephemeral"}
        }
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                    **cache_args
                },
                {"type": "text", "text": prompt_text}
            ]
        }
    ]
    if is_together:
        natural_response = completion_with_retries(
            messages=messages,
            model=model_name,
        )
        # print("natural response", natural_response.choices[0].message.content)

        # llama 3.2 doesn't support json output
        # so i need to take the output of llama 3.2 and conver it to json with llama 3.1
        # but I can't send the image to llama 3.1
        response = completion_with_retries(
            messages=[
                {
                    "role": "user",
                    "content": prompt_text
                },
                {
                    "role": "assistant",
                    "content": natural_response.choices[0].message.content
                },
                {
                    "role": "user",
                    "content": "write the fixes as json. Only output json."
                }
            ], model=hpc().json_converter_llm[len('litellm/'):], 
            response_format={
                "type": "json_object",
                "schema": FixResult.model_json_schema()
            })
    else:
        response_format = FixResult
        response = completion_with_retries(
            messages=messages,
            model=model_name,
            response_format=response_format
        )
    try:
        fixes_dict = json.loads(response.choices[0].message.content)
    except Exception as e:
        print('json loads error', response.choices[0].message.content)
        raise e
    if type(fixes_dict) == str:
        fixes_dict = json.loads(fixes_dict)
    try:
        if type(fixes_dict) == list:
            fixes = fixes_dict
        else:
            fixes = fixes_dict["fixes"]
    except TypeError as e:
        print('fixes_dict', fixes_dict)
        raise e
    except Exception as e:
        print('fixes_dict', fixes_dict)
        raise e

    # Prepare a list to collect fixes for each block.
    block_fixes = [[] for _ in blocks]
    try:
        # For each fix from the LLM, determine which block it applies to.
        for fix in fixes:
            line_number = fix["line_number"]
            for i, (start, num_lines) in enumerate(block_line_offsets):
                if start <= line_number < start + num_lines:
                    # Adjust fix line number relative to block (starting at 1).
                    adjusted_line_number = line_number - start + 1
                    block_fixes[i].append({
                        "line_number": adjusted_line_number,
                        "replacement": fix["replacement"]
                    })
                    break
    except Exception as e:
        print('error in block_fixes', fixes)
        raise e

    corrected_blocks = []
    # Apply fixes to each block separately.
    for block, fixes_for_block in zip(blocks, block_fixes):
        new_text = apply_fixes_to_text(block.text, fixes_for_block)
        corrected_blocks.append(PDFBlock(text=new_text, type=block.type, region=block.region))
    return corrected_blocks

def process_page(page_data, cache=False):
    """
    Process all blocks for a single page in parallel.
    """
    page_num, (page_blocks, img_b64) = page_data
    print(f"Processing page {page_num} with {len(page_blocks)} blocks")
    
    return [correct_page(page_blocks, img_b64, cache=cache)]

def post_correct(pdf_file_path: str, blocks: List[PDFBlock], strategy: str = "per_page") -> List[PDFBlock]:
    """
    Process PDFBlocks in parallel using ThreadPoolExecutor.

    The strategy parameter can be:
      - "per_block": each block is sent individually to the LLM.
      - "per_page": all blocks on each page are processed in a single LLM call.

    Returns the corrected PDFBlocks in the same order as they were received.
    """
    # Tag each block with its original index to preserve input order.
    indexed_blocks = list(enumerate(blocks))
    
    # Group blocks by their page number, preserving the original order per page.
    from collections import defaultdict
    blocks_by_page: dict[int, list[tuple[int, PDFBlock]]] = defaultdict(list)
    for idx, block in indexed_blocks:
        page_num = block.region.page_number
        if page_num is not None:
            blocks_by_page[page_num].append((idx, block))
    
    # Get the base64 images for the pages that have blocks.
    page_numbers = set(blocks_by_page.keys())
    images = get_page_images_as_base64(pdf_file_path, page_numbers)
    
    # Prepare page data: for each page number store a tuple consisting of:
    #   - the list of PDFBlocks (in their original order),
    #   - the corresponding base64 image,
    #   - the list of original indices for these blocks.
    page_data = {
        page_num: (
            [block for (_, block) in pairs],
            images.get(page_num),
            [idx for (idx, _) in pairs]
        )
        for page_num, pairs in blocks_by_page.items()
    }
    
    # This dict will store the corrected block for each original index.
    corrected_mapping = {}
    
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for page_num, (page_blocks, img_b64, indices) in page_data.items():
            if strategy == "per_page":
                # Processing all blocks on this page in one call.
                future = executor.submit(correct_page, page_blocks, img_b64)
            else:
                # Using process_page, which currently wraps correct_page.
                future = executor.submit(process_page, (page_num, (page_blocks, img_b64)), cache=(strategy == 'per_block'))
            futures[page_num] = (future, indices)
        
        # Collect results from all pages
        for page_num, (future, indices) in futures.items():
            result = future.result()
            # For the "per_block" strategy, process_page returns [correct_page(...)]
            corrections = result if strategy == "per_page" else result[0]
            # The returned corrections should be in the same order as page_blocks.
            for orig_idx, corrected_block in zip(indices, corrections):
                corrected_mapping[orig_idx] = corrected_block
    
    # Reassemble the corrected blocks in the original order.
    corrected_blocks = [corrected_mapping[i] for i in range(len(blocks))]
    return corrected_blocks
