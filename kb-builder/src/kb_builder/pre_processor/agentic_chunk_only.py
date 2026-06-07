"""
Agentic chunking using language models (no vision, no correction).
This module focuses only on intelligent text chunking without transcription correction.
"""

import dotenv
from kb_builder.load_env import load_env
load_env(override=True)
from litellm import completion_with_retries
from typing import List
from shared.logger import Logger
from kb_builder.pre_processor.marker_pdf import PDFBlock
from kb_builder.pre_processor.cached_correct import get_cached_completion, cache_completion
from kb_builder.hparams_config import hpc
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import re

# Unicode character for chunk delimiter
# CHUNK_DELIMITER = '✂️'
CHUNK_DELIMITER = '✂'
TOT_INPUT_TOKENS_USED = 0
TOT_OUTPUT_TOKENS_USED = 0
TOT_LLM_COST = 0
TOT_BLOCKS_PROCESSED = 0
TOT_BLOCKS_NOT_CACHED = 0


def generate_chunking_prompt(block_text: str) -> str:
    """
    Generates a prompt for text chunking only (no correction).
    """
    prompt = f"""Your task: Chunk the text below into sentence-like chunks by inserting {CHUNK_DELIMITER} characters at appropriate boundaries.

The text is already correctly transcribed, so DO NOT modify the content and do not remove line breaks. - only add {CHUNK_DELIMITER} characters for chunking.
You still have to keep the line breaks at the poins where you insert {CHUNK_DELIMITER}.

Rules:
- Most chunks should be sentences
- Some chunks could be headers, bullet points, or other logical units
- Chunks should neve be more than 100 words
- Insert {CHUNK_DELIMITER} character at appropriate chunk boundaries
- DO NOT modify the existing text content in any way
- DO NOT add, remove, or change any words
- ONLY add {CHUNK_DELIMITER} characters for chunking
- Output format: return ONLY the chunked text with {CHUNK_DELIMITER} delimiters, no explanations

Example:
`We attended the 1pm showing of Elio and showed up when the doors opened at 12:30pm so that we could ensure enough time for food to be ordered/delivered. We got to our seats, checked out the menu and placed an order around 12:45. 1:45 came and still no meal or drinks.`
becomes
`We attended the 1pm showing of Elio and showed up when the doors opened at 12:30pm so that we could ensure enough time for food to be ordered/delivered. {CHUNK_DELIMITER}We got to our seats, checked out the menu and placed an order around 12:45. {CHUNK_DELIMITER}1:45 came and still no meal or drinks.`
Here is an example with a line break that needs to be preserved.
`Before I left I closed out my tab outside of the theater and asked for a copy and it still had an item that never came that the server mentioned that they would remove. 
No issue, they removed it and my charge shows as the correct amount.`
becomes
`Before I left I closed out my tab outside of the theater and asked for a copy and it still had an item that never came that the server mentioned that they would remove. 
{CHUNK_DELIMITER}No issue, they removed it and my charge shows as the correct amount.`

Text to chunk:
{block_text}"""
    
    return prompt


def agentic_chunk_text(txt: str) -> str:
    """
    Chunks text using LLM without vision or correction.
    Returns the text with chunk delimiters inserted.
    """
    global TOT_INPUT_TOKENS_USED, TOT_OUTPUT_TOKENS_USED, TOT_LLM_COST, TOT_BLOCKS_NOT_CACHED
    
    # Helper: run agentic chunking on a single segment using the existing LLM flow
    def chunk_single_segment(segment_text: str) -> str:
        global TOT_INPUT_TOKENS_USED, TOT_OUTPUT_TOKENS_USED, TOT_LLM_COST, TOT_BLOCKS_NOT_CACHED
        # Skip very short text
        if len(segment_text.strip()) < 10:
            return segment_text
        
        prompt_text = generate_chunking_prompt(segment_text)
        model_name = hpc().agentic_chunk_llm[len('litellm/'):]
        temperature = 0.1  # Low temperature for consistent results
        
        messages = [
            {
                "role": "user",
                "content": prompt_text
            }
        ]
        
        # Check cache first
        cached_response = get_cached_completion(messages, model_name, temperature)
        did_cache_local = False
        
        # Validate cached response has content
        use_cached_local = False
        if cached_response is not None:
            try:
                cached_content = cached_response.choices[0].message.content
                if cached_content and cached_content.strip():
                    response_local = cached_response
                    did_cache_local = True
                    use_cached_local = True
                else:
                    Logger.warning("Cached response has empty content, making new API call")
            except (AttributeError, IndexError) as e:
                Logger.warning(f"Cached response has invalid structure, making new API call: {e}")
        
        if not use_cached_local:
            response_local = completion_with_retries(
                messages=messages,
                model=model_name,
                temperature=temperature,
                reasoning_effort='disable'
            )
            # Track usage and cost
            TOT_INPUT_TOKENS_USED += response_local.usage.prompt_tokens
            TOT_OUTPUT_TOKENS_USED += response_local.usage.completion_tokens
            TOT_BLOCKS_NOT_CACHED += 1
            hidden_params = response_local._hidden_params
            TOT_LLM_COST += hidden_params['response_cost']
            # Cache the response
            cache_completion(messages, model_name, temperature, response_local)

        try:
            output_local = response_local.choices[0].message.content
        except Exception as e:
            Logger.error(f"Error getting output from agentic chunking: {e}")
            raise
            
        if not output_local:
            Logger.error(f"No output from agentic chunking: {response_local}")
            raise Exception(f"No output from agentic chunking: {response_local} did_cache: {did_cache_local}")

        # Ensure that removing delimiters yields the original segment text
        if re.sub(r'✂️|✂', '', output_local) != segment_text:
            open('/tmp/mismatch.txt', 'a').write(f"Input: {segment_text}\nOutput: {output_local}")
            print("WARNING: Output text does not match input text")

        return output_local

    # Define a regex that identifies two or more line breaks in a row.
    # A line break can be a newline (\n) or an HTML <br> / <br/> tag, with optional whitespace between.
    br_token = r'(?:\n|<br\s*/?>)'
    double_break_pattern = rf'(?:\s*{br_token}\s*){{2,}}'

    # Split while keeping the delimiters so we can reassemble exactly
    parts = re.split(f'({double_break_pattern})', txt)

    # If no double-break delimiters found, just chunk the whole text
    if len(parts) == 1:
        return chunk_single_segment(txt)

    # Otherwise, chunk only the text parts (even indices), keep delimiters untouched (odd indices)
    result_parts: List[str] = []
    for idx, part in enumerate(parts):
        if idx % 2 == 1:
            # This is a delimiter (the matched double-break sequence) — preserve exactly
            result_parts.append(part)
        else:
            # Text segment between delimiters
            if part == '':
                result_parts.append(part)
            else:
                result_parts.append(chunk_single_segment(part))

    # Reassemble; removing chunk delimiters should restore original text
    output = ''.join(result_parts)
    if re.sub(r'✂️|✂', '', output) != txt:
        open('/tmp/mismatch.txt', 'a').write(f"Input: {txt}\nOutput: {output}")
        print("WARNING: Output text does not match input text after segmentation")

    return output


def agentic_chunk_block(block: PDFBlock) -> PDFBlock:
    """
    Chunks a single block using LLM without vision or correction.
    Returns the block with chunk delimiters inserted.
    """
    # Use the helper function to chunk the text
    chunked_text = agentic_chunk_text(block.text)
    
    # Create new block with chunked text
    new_block = PDFBlock(
        text=chunked_text,
        type=block.type,
        region=block.region
    )
    
    return new_block


def agentic_chunk_only(blocks: List[PDFBlock]) -> List[PDFBlock]:
    """
    Process PDFBlocks using agentic chunking only (no correction, no vision).
    Each block is processed individually to determine chunk boundaries.
    Returns PDFBlocks where each block contains chunk delimiters.
    """
    from shared.hparams_config import hpc as shared_hpc
    
    # Get the list of block types that should not be chunked
    no_chunk_types = shared_hpc().NO_CHUNK_BLOCK_TYPES
    
    # Filter blocks that need processing (excluding no-chunk types)
    blocks_to_process = [(i, block) for i, block in enumerate(blocks) if block.type not in no_chunk_types]
    
    Logger.info(f"Processing {len(blocks_to_process)} blocks out of {len(blocks)} total blocks")
    Logger.info(f"Skipping block types: {set(block.type for _, block in enumerate(blocks) if block.type in no_chunk_types)}")
    
    # If no blocks need processing, return original blocks
    if not blocks_to_process:
        return blocks
    
    # Process blocks in parallel
    processed_blocks_by_idx = {}
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        
        for original_idx, block in blocks_to_process:
            future = executor.submit(agentic_chunk_block, block)
            futures.append((original_idx, block, future))
        
        # Collect results
        for original_idx, original_block, future in (futures):
            def fallback_to_spacy():
                """Fallback to spacy sentence splitting when agentic chunking fails"""
                Logger.info(f"Falling back to spacy sentence splitting for block {original_idx}")
                
                # Import spacy sentence splitter from chunker module
                from kb_builder.vectorize.chunker import spacy_sentence_split
                
                # Use spacy to split the block text into sentences
                sentences = spacy_sentence_split(original_block.text)
                
                # Join sentences back with chunk delimiter
                chunked_text = CHUNK_DELIMITER.join(sentences)
                
                # Create new block with chunked text
                new_block = PDFBlock(
                    text=chunked_text,
                    type=original_block.type,
                    region=original_block.region
                )
                processed_blocks_by_idx[original_idx] = new_block

            try:
                chunked_block = future.result()
                processed_blocks_by_idx[original_idx] = chunked_block
                
            except Exception as e:
                Logger.warning(f"Error processing block {original_idx}: {e}")
                fallback_to_spacy()

    # Reconstruct the full block list in original order
    result_blocks = []
    for i, original_block in enumerate(blocks):
        if i in processed_blocks_by_idx:
            # This block was processed - use the processed version
            result_blocks.append(processed_blocks_by_idx[i])
        else:
            # This block was skipped (no-chunk type) - keep original
            result_blocks.append(original_block)
    
    # Count total chunks
    tot_num_chunks = 0
    for block in result_blocks:
        if block.type not in no_chunk_types:
            tot_num_chunks += len(block.text.split(CHUNK_DELIMITER))
    
    Logger.info(f"Total chunks created: {tot_num_chunks}")
    
    global TOT_BLOCKS_PROCESSED
    TOT_BLOCKS_PROCESSED += len(blocks_to_process)
    
    Logger.info(f"Processing stats: cost=${TOT_LLM_COST:.4f}, input_tokens={TOT_INPUT_TOKENS_USED}, "
               f"output_tokens={TOT_OUTPUT_TOKENS_USED}, blocks_processed={TOT_BLOCKS_PROCESSED}, "
               f"blocks_not_cached={TOT_BLOCKS_NOT_CACHED}")
    
    return result_blocks 