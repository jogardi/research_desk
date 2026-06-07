"""
Agentic chunking and post-correction using vision language models.
This module combines transcription correction and intelligent chunking in a single VLM call.
"""

import dotenv
from kb_builder.load_env import load_env
load_env(override=True)
from litellm import completion_with_retries
from typing import List, Iterable
from shared.logger import Logger
from kb_builder.pre_processor.marker_pdf import PDFBlock
from kb_builder.pre_processor.cached_correct import get_cached_completion, cache_completion
from kb_builder.hparams_config import hpc
import pdfplumber
from concurrent.futures import ThreadPoolExecutor
import io
import re

# Unicode character for chunk delimiter
CHUNK_DELIMITER = '✂'  # U+001E Record Separator
TOT_PIXELS = 0
TOT_INPUT_TOKENS_USED = 0
TOT_OUTPUT_TOKENS_USED = 0
TOT_LLM_COST = 0
TOT_PAGES_PROCESSED = 0
TOT_PAGES_NOT_CACHED = 0


def pdf_to_images(pdf_path, resolution=164) -> Iterable[bytes]:
    """
    Yields each PDF page as a PIL Image.
    :param pdf_path: Path to your PDF file.
    :param resolution: DPI for rendering pages to images (higher = bigger image).
    """
    global TOT_PIXELS
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            # Convert page to an in-memory image
            page_image = page.to_image(resolution=resolution)
            
            # Print dimensions of the page image
            width, height = page_image.original.size
            TOT_PIXELS += width*height
            # print(f"Page {page_index + 1}: {width}x{height}, {width*height} pixels. Total: {TOT_PIXELS} pixels.")
            
            # Save image to a BytesIO buffer
            img_buffer = io.BytesIO()
            page_image.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            # also save to /tmp/page_images/
            # import os
            # os.makedirs('/tmp/page_images/', exist_ok=True)
            # page_image.save(f'/tmp/page_images/page_{page_index + 1}.png')
            
            yield img_buffer

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

def introduce_random_errors(text: str) -> str:
    """
    Introduce random small errors to test correction functionality.
    """
    import random
    
    # Skip if text is very short or just whitespace
    if len(text.strip()) < 5:
        return text
    
    # Convert to list for easier manipulation
    chars = list(text)
    
    # Define error types and their probabilities
    error_types = []
    
    # 1. Character substitutions (OCR-like errors)
    if random.random() < 0.3:  # 30% chance
        substitutions = {
            'e': '3', 'E': '3',
            'o': '0', 'O': '0', 
            'l': '1', 'I': '1',
            'a': '@',
            's': '5', 'S': '5',
            'g': '9',
            'b': '6',
        }
        # Find substitutable characters
        substitutable = [(i, c) for i, c in enumerate(chars) if c in substitutions]
        if substitutable:
            idx, char = random.choice(substitutable)
            chars[idx] = substitutions[char]
    
    # 2. Missing character (10% chance)
    if random.random() < 0.1 and len(chars) > 10:
        # Remove a random character (not from the very beginning or end)
        idx = random.randint(5, len(chars) - 5)
        if chars[idx] not in ' \n\t':  # Don't remove whitespace
            chars.pop(idx)
    
    # 3. Extra character (10% chance)
    if random.random() < 0.1 and len(chars) > 10:
        # Add an extra character
        idx = random.randint(5, len(chars) - 5)
        # Duplicate the character at that position
        if chars[idx] not in ' \n\t':
            chars.insert(idx, chars[idx])
    
    # 4. Capitalization error (15% chance)
    if random.random() < 0.15:
        # Find alphabetic characters
        alpha_indices = [i for i, c in enumerate(chars) if c.isalpha()]
        if alpha_indices:
            idx = random.choice(alpha_indices)
            chars[idx] = chars[idx].swapcase()
    
    # 5. Common misspellings (20% chance)
    if random.random() < 0.2:
        common_errors = [
            ('the', 'teh'),
            ('and', 'adn'),
            ('with', 'wiht'),
            ('have', 'haev'),
            ('from', 'form'),
            ('that', 'taht'),
            ('been', 'bene'),
            ('their', 'thier'),
            ('would', 'woudl'),
            ('which', 'whihc'),
        ]
        result_text = ''.join(chars)
        for correct, error in common_errors:
            if correct in result_text.lower():
                # Case-insensitive replacement
                import re
                result_text = re.sub(r'\b' + correct + r'\b', error, result_text, count=1, flags=re.IGNORECASE)
                return result_text
    
    return ''.join(chars)

def generate_agentic_prompt(blocks: List[PDFBlock]) -> str:
    """
    Generates a prompt for agentic chunking and correction.
    Blocks are separated by the marker separator.
    """
    # Join blocks with the separator, adding index prefixes
    indexed_blocks = []
    for i, block in enumerate(blocks):
        # Introduce random errors to test correction
        # text_with_errors = introduce_random_errors(block.text)
        indexed_blocks.append(f"{i}: {block.text}")
    
    blocks_text = "\n\n☐\n\n".join(indexed_blocks)
    
    prompt = f"""Your task: The text below is a transcription of a page of a pdf.
The transcription is html so that the original formatting can be preserved as much as possible (e.g. bolding, interpuncts, nested lists). 
Correct transcription/formatting errors and chunk the text into sentence like chunks. 
You can see the image of the page so that you can see where the transcription does not match the image.
Most of the chunks should be sentences. Some could be headers, or bullet points. 
Process the text below by correcting transcription errors and adding {CHUNK_DELIMITER} characters to mark appropriate chunk boundaries. So then the system will 
take each block of your output and get the chunks as `chunks = corrected_block.split('{CHUNK_DELIMITER}')`.

rules:
- ONLY correct transcription errors in the existing text blocks
- DO NOT add any missing content or new blocks that you see in the image
- You must output exactly the same number of blocks as the input
- Each input block must correspond to exactly one output block
- If there is a table of contents, dot leaders and page numbers should not be included in the transcription.
- don't worry about chunking html tables
- You may need to put `<br/>` where a line break is missing but it makes sense for a line break to be missing if the line break was due to text wrapping
- A common transcription error is to have something like `&amp;lt;sup&gt;83</sup>` where it should be `<sup>83</sup>`
- latex must be surrouneded by <math> tags. Math should be formatted as latex. 

IMPORTANT: The input contains multiple text blocks separated by ☐. Each block starts with an index number. You must preserve this exact structure in your output, including the index numbers.
Output format:
- Return ONLY the processed text
- NO explanations
- Keep ALL ☐ separators with their newlines
- Keep ALL index numbers (0:, 1:, 2:, etc.) exactly as shown
- Use actual {CHUNK_DELIMITER} character, not placeholders
- Output exactly {len(blocks)} blocks, no more, no less

Here is an example showing how to chunk:
```
0: The source document has several sentences in one block. The first idea should stand alone. The second idea should become a separate chunk.

☐

1: Another block already contains a single coherent idea.
```
becomes

```
0: The source document has several sentences in one block. {CHUNK_DELIMITER}The first idea should stand alone. {CHUNK_DELIMITER}The second idea should become a separate chunk.

☐

1: Another block already contains a single coherent idea.
```
In the given example there were no transcription errors, but the text was chunked.

Here is an example with math:
```
️The formula is
\\Gamma = 19.53 \\ E \\ I \\left(\\frac{{\\mu_{{en}}}}{{\\rho}}\\right)<br/>
where \\rho is a constant.
```
becomes
```
️The formula is<br/>
<math>\\Gamma = 19.53 \\ E \\ I \\left(\\frac{{\\mu_{{en}}}}{{\\rho}}\\right)</math><br/>
where <math>\\rho</math> is a constant.
```

For the transcription below, you are able to see the image of the page so that you can not only chunk but also correct whatever transcription errors are there.

Input text:
{blocks_text}"""
    
    return prompt

def agentic_correct_and_chunk_page(blocks: List[PDFBlock], img_b64: str, pdf_file_path: str = "", page_num: int = 0) -> str:
    """
    Corrects and chunks all blocks on a page in one VLM call.
    Returns the corrected text with chunk delimiters inserted.
    """
    global TOT_INPUT_TOKENS_USED, TOT_OUTPUT_TOKENS_USED, TOT_LLM_COST, TOT_PAGES_NOT_CACHED
    prompt_text = generate_agentic_prompt(blocks)
    model_name = hpc().agentic_chunk_llm[len('litellm/'):]
    temperature = 0.1  # Low temperature for consistent results
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                },
                {"type": "text", "text": prompt_text}
            ]
        }
    ]
    # print("prompt text: ", prompt_text)
    
    # Check cache first
    cached_response = get_cached_completion(messages, model_name, temperature)
    did_cache = False
    
    # Validate cached response has content
    use_cached = False
    if cached_response is not None:
        try:
            cached_content = cached_response.choices[0].message.content
            if cached_content and cached_content.strip():
                print(f"Using cached response for page {page_num}")
                response = cached_response
                did_cache = True
                use_cached = True
            else:
                print(f"Cached response for page {page_num} has empty content, making new API call")
        except (AttributeError, IndexError) as e:
            print(f"Cached response for page {page_num} has invalid structure, making new API call: {e}")
    
    if not use_cached:
        response = completion_with_retries(
            messages=messages,
            model=model_name,
            temperature=temperature,
            # reasoning_effort='disable'
        )
        TOT_INPUT_TOKENS_USED += response.usage.prompt_tokens
        TOT_OUTPUT_TOKENS_USED += response.usage.completion_tokens
        TOT_PAGES_NOT_CACHED += 1
        hidden_params = response._hidden_params
        TOT_LLM_COST += hidden_params['response_cost']
        # Cache the response
        cache_completion(messages, model_name, temperature, response)
    

    try:
        output = response.choices[0].message.content
    except Exception as e:
        print("Error getting output from agentic chunking", response)
    if not output:
        print("No output from agentic chunking", response)
        raise Exception(f"No output from agentic chunking: {response} did_cache: {did_cache}")

    
    # Write both input and output to chat record
    from shared.config import cfg
    import os
    log_folder = cfg().LOG_FOLDER
    
    with open(os.path.join(log_folder, 'agentic_chat_record.txt'), 'a') as f:
        f.write(f"PDF: {pdf_file_path} page: {page_num}\n")
        f.write("input: " + prompt_text + '\n=========\n' + "output: " + output + '\n=========\n\n')
    return output

def split_chunked_text_to_blocks(chunked_text: str, original_blocks: List[PDFBlock]) -> List[PDFBlock]:
    """
    Takes the chunked text output and splits it back into PDFBlocks.
    Each chunk becomes a separate block, preserving original metadata.
    """
    # Split by block separator first
    block_texts = chunked_text.split("\n☐\n")
    
    if len(block_texts) != len(original_blocks):
        print(f"Error: Block count mismatch. Original: {len(original_blocks)}, Processed: {len(block_texts)}")
        print(f"Number of separators found: {chunked_text.count('☐')}")
        print(f"Response preview: {chunked_text}...")
        print("original blocks: ", '\n=====\n'.join([b.text for b in original_blocks]))
        raise ValueError(
            f"Agentic chunking failed to preserve block structure. "
            f"Expected {len(original_blocks)} blocks but got {len(block_texts)}. "
            f"The model must preserve all ☐ separators."
        )
    
    # Process each block
    new_blocks = []
    for i, (block_text, original_block) in enumerate(zip(block_texts, original_blocks)):
        # Create a new PDFBlock with the text containing chunk delimiters
        # Do NOT split by chunk delimiter - that happens later in chunker.py
        block_text = block_text.strip()
        # Remove index prefix (e.g., "0: ", "1: ", etc.)
        # Find the first colon and space after a number
        match = re.match(r'^\d+:\s*', block_text)
        if match:
            # Assert that the index prefix matches the expected index
            expected_index = int(match.group().rstrip(': '))
            assert expected_index == i, f"Index mismatch: expected {i} but got {expected_index} in block text: {block_text[:100]}..."
            # Remove the index prefix
            block_text = block_text[match.end():]
        

        assert block_text, f"Empty block text: {block_text}\n Original block: {original_block.text}"
        # if block_text:  # Skip empty blocks
        new_block = PDFBlock(
            text=block_text,
            type=original_block.type,
            region=original_block.region
        )
        new_blocks.append(new_block)
    
    return new_blocks

def agentic_chunk_correct(pdf_file_path: str, blocks: List[PDFBlock]) -> List[PDFBlock]:
    """
    Process PDFBlocks using agentic chunking and correction.
    Each page is processed to both correct transcription errors and determine chunk boundaries.
    Returns PDFBlocks where each block represents a chunk.
    """
    from shared.hparams_config import hpc as shared_hpc
    
    # Get the list of block types that should not be chunked
    no_chunk_types = shared_hpc().NO_CHUNK_BLOCK_TYPES
    
    print(f"Processing {len(blocks)} blocks")
    print(f"Skipping block types: {set(block.type for _, block in enumerate(blocks) if block.type in no_chunk_types)}")
    
    # If no blocks need processing, return original blocks
    if not blocks:
        return blocks
    
    # Group blocks by page
    from collections import defaultdict
    blocks_by_page = defaultdict(list)
    
    for original_idx, block in enumerate(blocks):
        page_num = block.region.page_number
        if page_num is not None:
            blocks_by_page[page_num].append((original_idx, block))
    
    # Get page images
    page_numbers = set(blocks_by_page.keys())
    images = get_page_images_as_base64(pdf_file_path, page_numbers)
    
    # Process each page and store results indexed by original position
    processed_blocks_by_idx = {}
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        
        for page_num in sorted(blocks_by_page.keys()):
            page_data = blocks_by_page[page_num]
            page_blocks = [block for _, block in page_data]
            original_indices = [idx for idx, _ in page_data]
            img_b64 = images[page_num]
            
            future = executor.submit(
                agentic_correct_and_chunk_page,
                page_blocks,
                img_b64,
                pdf_file_path,
                page_num
            )
            futures.append((page_num, page_blocks, original_indices, future))
        
        # Collect results
        for page_num, original_page_blocks, original_indices, future in futures:
            def fallback_to_spacy():
                """Fallback to spacy sentence splitting when agentic chunking fails"""
                Logger.info(f"Falling back to spacy sentence splitting for page {page_num}")
                print(f"Falling back to spacy sentence splitting for page {page_num}")
                
                # Import spacy sentence splitter from chunker module
                from kb_builder.vectorize.chunker import spacy_sentence_split
                
                # Process each block individually using spacy
                for orig_idx, block in zip(original_indices, original_page_blocks):
                    # Skip spaCy processing for blocks with no_chunk_types
                    if block.type in no_chunk_types:
                        # Use original text without any processing
                        new_block = PDFBlock(
                            text=block.text,
                            type=block.type,
                            region=block.region
                        )
                        processed_blocks_by_idx[orig_idx] = new_block
                    else:
                        # Use spacy to split the block text into sentences
                        sentences = spacy_sentence_split(block.text)
                        
                        # Join sentences back with chunk delimiter
                        chunked_text = CHUNK_DELIMITER.join(sentences)
                        
                        # Create new block with chunked text
                        new_block = PDFBlock(
                            text=chunked_text,
                            type=block.type,
                            region=block.region
                        )
                        processed_blocks_by_idx[orig_idx] = new_block
                    if len([x for x in re.split(CHUNK_DELIMITER, new_block.text) if x.strip()]) == 0:
                        print("empty block", new_block)
                        print("original block: ", block)
                        raise ValueError("empty block")

            try:
                chunked_text = future.result()
                # Convert chunked text back to blocks
                chunked_blocks = split_chunked_text_to_blocks(chunked_text, original_page_blocks)
                
                # Map processed blocks back to their original indices
                for orig_idx, chunked_block, original_block in zip(original_indices, chunked_blocks, original_page_blocks):
                    # For blocks with no_chunk_types, ignore the model's output and use original text
                    if original_block.type in no_chunk_types:
                        processed_blocks_by_idx[orig_idx] = original_block
                    else:
                        processed_blocks_by_idx[orig_idx] = chunked_block
                    new_block = chunked_block
                    if len([x for x in re.split(CHUNK_DELIMITER, new_block.text) if x.strip()]) == 0:
                        print("empty block", new_block)
                        print("original block: ", block)
                        exit(1)

            except ValueError as ve:
                # Re-raise ValueError with page information
                Logger.warning(f"Value Error processing Page {page_num}: {str(ve)}")
                fallback_to_spacy()
            except Exception as e:
                Logger.warning(f"Error processing page {page_num}: {e}")
                fallback_to_spacy()

    # Reconstruct the full block list in original order
    result_blocks = []
    for i, original_block in enumerate(blocks):
        assert i in processed_blocks_by_idx
        # This block was processed - use the processed version
        result_blocks.append(processed_blocks_by_idx[i])
        # else:
        #     result_blocks.append(original_block)
    
    tot_num_chunks = 0
    for block in result_blocks:
        if block.type not in no_chunk_types:
            tot_num_chunks += len(block.text.split(CHUNK_DELIMITER))
    print('tot num chunks: ', tot_num_chunks)
    global TOT_PAGES_PROCESSED
    TOT_PAGES_PROCESSED += len(page_numbers)
    
    Logger.info(f"tot costs so far: {TOT_LLM_COST=}, {TOT_INPUT_TOKENS_USED=}, {TOT_OUTPUT_TOKENS_USED=} {TOT_PIXELS=}, {TOT_PAGES_PROCESSED=}, {TOT_PAGES_NOT_CACHED=}")
    
    return result_blocks 
