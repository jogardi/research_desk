import pdfplumber
import requests
from io import BytesIO

from pathlib import Path

from shared.config import Config    
from shared.logger import Logger

import requests
import pdfplumber
from io import BytesIO

#depracated
def find_phrase_in_pdf(pdf_url, phrase) -> int:
    print(f'+++++++++ pdf_url: {pdf_url}')
    print(f'+++++++++ phrase: {phrase}')
    # Download the PDF from a URL
    response = requests.get(pdf_url)
    response.raise_for_status()
    pdf_file = BytesIO(response.content)

    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            words = page.extract_words()
            
            # Split the phrase into individual words
            phrase_words = phrase.split()
            phrase_length = len(phrase_words)

            # Iterate through the words and check for a sequence match
            for i in range(len(words) - phrase_length + 1):
                match = True
                for j in range(phrase_length):
                    if words[i + j]['text'] != phrase_words[j]:
                        match = False
                        break
                
                # If a match is found, return the current page number
                if match:
                    return page_num
    
    # If the phrase is not found in the entire document, return -1 or any other indicator
    return -1




# Example usage
pdf_url = "https://example.com/sample.pdf"
phrase = "sample phrase"
# page_number, positions = find_phrase_in_pdf(pdf_url, phrase)

# if page_number:
#     print(f"Phrase '{phrase}' found on page {page_number} at positions:")
#     for pos in positions:
#         print(pos)
# else:
#     print(f"Phrase '{phrase}' not found in the document.")

