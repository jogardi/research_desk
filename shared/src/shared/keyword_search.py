import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import logging
from functools import lru_cache
from pathlib import Path

def our_stopwords():
    return [
        'instance',
        'instances',
        'examples',
    ]


@lru_cache()
def get_stopwords():
    # Download required NLTK data if not already present
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

    our_set = set(stopwords.words('english'))
    our_set.update(our_stopwords())
    our_set.update(open(Path(__file__).parent / 'stopwords.txt').read().splitlines())
    return our_set


def nltk_remove_stopwords(txt: str) -> str:
    """
    Remove stopwords from text using NLTK.
    
    Args:
        txt (str): Input text to process
        
    Returns:
        str: Text with stopwords removed
        
    Raises:
        Exception: If NLTK data is not available or tokenization fails
    """
    if not txt or not txt.strip():
        return txt

    try:
        # Tokenize the text
        tokens = word_tokenize(txt.lower())
        
        # Get stopwords
        stop_words = get_stopwords()
        # Remove stopwords and join back into text
        filtered_tokens = [word for word in tokens if word not in stop_words]
        
        return ' '.join(filtered_tokens)
        
    except Exception as e:
        logging.error(f"Error removing stopwords: {e}")
        raise Exception(f"Failed to remove stopwords from text: {e}")
