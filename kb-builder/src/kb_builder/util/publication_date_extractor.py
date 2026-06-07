#!/usr/bin/env python3
"""
Utility module for extracting publication dates from document blocks during processing.
"""

import json
import os
from typing import Optional, List, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import litellm
from pydantic import BaseModel
from shared.logger import Logger
from shared.cache import mem
from kb_builder.pre_processor.pdf_block import PDFBlock
from kb_builder.pre_processor.video_block import VideoBlock


class PublicationDateResult(BaseModel):
    """Structured output model for publication date extraction"""
    has_publication_date: bool
    publication_date: Optional[str] = None  # Format: YYYY-MM-DD
    confidence: str  # "high", "medium", "low"
    reasoning: str


def extract_publication_date_from_blocks(blocks: List[Union[PDFBlock, VideoBlock]], file_name: str) -> Optional[str]:
    """
    Extract publication date from document blocks during processing.
    
    Args:
        blocks: List of PDFBlock or VideoBlock objects
        file_name: Name of the file being processed
        
    Returns:
        Publication date in YYYY-MM-DD format or None if not found
    """
    try:
        # Get text from first few blocks (first 3 pages or equivalent)
        first_blocks_text = []
        
        for block in blocks[:60]:  # Limit to first 60 blocks
            # For PDF blocks, check if it's from first 3 pages
            if hasattr(block.region, 'page_number'):
                if block.region.page_number <= 3:
                    first_blocks_text.append(block.text)
            else:
                # For other block types, just include first blocks
                first_blocks_text.append(block.text)
        
        if not first_blocks_text:
            Logger.warning(f"No blocks found for publication date extraction: {file_name}")
            return None
        
        # Combine text from blocks
        text = '\n'.join(first_blocks_text)
        
        # Extract publication date using AI (with caching)
        result = _extract_publication_date_ai(text, file_name)
        
        if result.has_publication_date and result.publication_date:
            Logger.info(f"Extracted publication date for {file_name}: {result.publication_date} (confidence: {result.confidence})")
            return result.publication_date
        else:
            Logger.info(f"No publication date found for {file_name}: {result.reasoning}")
            return None
            
    except Exception as e:
        Logger.error_formatted(f"Error extracting publication date for {file_name}", e)
        return None


@mem()
def _extract_publication_date_ai_cached(text: str, file_name: str) -> dict:
    """Cached version of AI publication date extraction that returns a dict for serialization"""
    
    prompt = f"""Analyze the following text from the first 3 pages of a document titled "{file_name}" and extract the publication date if present.

Text to analyze:
{text[:200_000]}  # Limit text to avoid token limits

Instructions:
1. Look for explicit publication dates, copyright dates, or dates when the document was published/released
2. Common patterns include: "Published on", "Publication Date:", copyright symbols with years, dates in headers/footers
3. If no date is found in the content, check if the filename contains a clear date reference (e.g., "December-2021", "2024", etc.)
4. If multiple dates are found, prefer the most recent publication/revision date
5. Convert any date found to YYYY-MM-DD format
6. If only a year is found, use YYYY-01-01 (January 1st as default)
7. If only month and year are found, use YYYY-MM-01 (1st day of the month as default)

Return a JSON object with:
- has_publication_date: boolean indicating if a date was found
- publication_date: the date in YYYY-MM-DD format (null if not found)
- confidence: "high" (explicit publication date), "medium" (copyright or inferred date), or "low" (uncertain)
- reasoning: brief explanation of how the date was determined or why none was found
"""

    try:
        # Use Claude Sonnet 4 model
        model = "claude-sonnet-4-20250514"
        
        # Determine response format based on model
        if model.startswith('together_ai'):
            response_format = {
                "type": "json_object",
                'schema': PublicationDateResult.model_json_schema()
            }
        else:
            response_format = PublicationDateResult     
        
        # Make the API call with structured output
        response = litellm.completion_with_retries(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format=response_format,
            temperature=0.1  # Low temperature for more consistent results
        )
        
        # Parse the response
        response_content = response.choices[0].message.content
        result = json.loads(response_content)
        
        # Handle different response formats
        if 'properties' in result:
            # Claude sometimes wraps the response in a properties key
            result = result['properties']
        
        return result
    
    except Exception as e:
        Logger.error_formatted(f"Error in AI publication date extraction for {file_name}", e)
        # Return a default result on error
        return {
            "has_publication_date": False,
            "publication_date": None,
            "confidence": "low",
            "reasoning": f"Error during extraction: {str(e)}"
        }


def _extract_publication_date_ai(text: str, file_name: str) -> PublicationDateResult:
    """Extract publication date from text using Claude Sonnet via litellm with caching"""
    
    try:
        # Use the cached function and convert result back to Pydantic model
        result_dict = _extract_publication_date_ai_cached(text, file_name)
        return PublicationDateResult(**result_dict)
    
    except Exception as e:
        Logger.error_formatted(f"Error in AI publication date extraction for {file_name}", e)
        # Return a default result on error
        return PublicationDateResult(
            has_publication_date=False,
            publication_date=None,
            confidence="low",
            reasoning=f"Error during extraction: {str(e)}"
        ) 
