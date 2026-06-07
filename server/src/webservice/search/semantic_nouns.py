import spacy
import re
from sentence_transformers import util
from webservice.keywords import getKeywords
from shared.utils import timing
import torch
from shared.keyword_search import nltk_remove_stopwords
from shared import keyword_search


# Load spaCy model for noun extraction
def load_nlp():
    return spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])


try:
    nlp = load_nlp()
except OSError:
    print("Downloading spaCy en_core_web_sm model...")
    spacy.cli.download("en_core_web_sm")
    # Try loading again after download
    nlp = load_nlp()

def get_query_embedding(query, model):
    return model.encode(query, convert_to_tensor=True)
    
def get_semantic_nouns(query, query_embedding, text, model):
    from bs4 import BeautifulSoup
    
    # First, get FTS-style keywords from the query
    fts_keywords = getKeywords(query, is_fts=False)
    
    # Parse the HTML content
    soup = BeautifulSoup(text, "html.parser")
    # Extract the text content from the parsed HTML
    text_content = soup.get_text()
    # text_content = text
    
    # Process the extracted text with spaCy
    doc = nlp(text_content)
    
    # Extract nouns, adjectives, verbs, etc.
    nouns = [token.text for token in doc if token.pos_ == "NOUN" or token.pos_ == "PROPN" or token.pos_ == "ADJ" or token.pos_ == "ADV" or token.pos_ == "VERB"]
    # remove special characters from each noun
    nouns = [re.sub(r'[^\w\s]', '', noun) for noun in nouns]

    if not nouns:
        return []  # No nouns found

    # Compute embeddings
    noun_embeddings = model.encode(nouns, convert_to_tensor=True)
 
    # Compute similarity scores
    scores = util.pytorch_cos_sim(query_embedding, noun_embeddings)[0].tolist()
    
    # Rank nouns by relevance
    ranked_nouns = sorted(zip(nouns, scores), key=lambda x: x[1], reverse=True)
    # filter out nouns with a score less than .35
    ranked_nouns = [(noun, score) for noun, score in ranked_nouns if score > .35]

    return [noun for noun, score in ranked_nouns] + fts_keywords

def get_semantic_nouns_111(query, query_embedding, text, model):
    from bs4 import BeautifulSoup
    
    # First, get FTS-style keywords from the query
    fts_keywords = getKeywords(query, is_fts=False)
    
    # Parse the HTML content
    soup = BeautifulSoup(text, "html.parser")
    # Extract the text content from the parsed HTML
    text_content = soup.get_text()
    
    # Process the extracted text with spaCy
    doc = nlp(text_content)
    
    # Extract nouns, adjectives, verbs, etc. with early filtering
    nouns = []
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN", "ADJ", "ADV", "VERB"]:
            # Early filtering: only keep nouns with length > 2
            if len(token.text) > 2:
                # Remove special characters
                clean_noun = re.sub(r'[^\w\s]', '', token.text)
                if len(clean_noun) > 2:  # Check again after cleaning
                    nouns.append(clean_noun)
    
    # Remove duplicates (first optimization)
    nouns = list(set(nouns))

    if not nouns:
        return []  # No nouns found

    # Compute embeddings
    noun_embeddings = model.encode(nouns, convert_to_tensor=True)
 
    # Compute similarity scores
    scores = util.pytorch_cos_sim(query_embedding, noun_embeddings)[0].tolist()
    
    # Rank nouns by relevance
    ranked_nouns = sorted(zip(nouns, scores), key=lambda x: x[1], reverse=True)
    # filter out nouns with a score less than .35
    ranked_nouns = [(noun, score) for noun, score in ranked_nouns if score > .35]

    return [noun for noun, score in ranked_nouns] + fts_keywords

def get_semantic_nouns_222(query, query_embedding, text, model):
    from bs4 import BeautifulSoup
    
    # First, get FTS-style keywords from the query
    fts_keywords = getKeywords(query, is_fts=False)
    
    # Parse the HTML content
    soup = BeautifulSoup(text, "html.parser")
    # Extract the text content from the parsed HTML
    text_content = soup.get_text()
    
    # Process the extracted text with spaCy
    with timing('nlp'):
        doc = nlp(text_content)
        
    # Extract nouns, adjectives, verbs, etc. with minimal filtering
    nouns = []
    noun_counts = {}
    ntoks = len(doc)
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN", "ADJ", "ADV", "VERB"]:
            # Only filter out very short tokens (1 character) and stopwords
            if len(token.text) > 1 and not token.is_stop and token.text not in keyword_search.get_stopwords():
                # Remove special characters but keep more content
                clean_noun = re.sub(r'[^\w\s]', '', token.text)
                if len(clean_noun) > 1:  # More permissive length check
                    nouns.append(clean_noun)
                    noun_counts[clean_noun] = noun_counts.get(clean_noun, 0) + 1
    
    # Remove duplicates but keep more nouns
    nouns = list(set(nouns))
    num_nouns = len(nouns)

    if not nouns:
        return []  # No nouns found

    # Compute embeddings with batch size optimization for CPU
    #Use MPS if available, otherwise fall back to CPU
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    noun_embeddings = model.encode(nouns, batch_size=512, convert_to_tensor=True, device=device)
 
    # Compute similarity scores
    scores = util.pytorch_cos_sim(query_embedding, noun_embeddings)[0].tolist()
    
    # Rank nouns by relevance
    ranked_nouns = sorted(zip(nouns, scores), key=lambda x: x[1], reverse=True)
    # More permissive score threshold
    ranked_nouns = [(noun, score) for noun, score in ranked_nouns if score > .5]
    MAX_PORTION_BOLDED=.1
    if len(ranked_nouns) > 3:
        # Count instances of each noun in the text to ensure we don't exceed MAX_PORTION_BOLDED
        max_bolded_words = int(MAX_PORTION_BOLDED * ntoks)
        
        # Select nouns greedily until we reach the limit
        selected_nouns = []
        total_bolded_count = 0
        
        for noun, score in ranked_nouns:
            noun_count = noun_counts[noun]
            if total_bolded_count + noun_count <= max_bolded_words:
                selected_nouns.append(noun)
                total_bolded_count += noun_count
            else:
                # Stop adding nouns to avoid exceeding the limit
                break
        
        return selected_nouns + fts_keywords
    
    return [noun for noun, score in ranked_nouns] + fts_keywords

def get_semantic_nouns_batch(query, query_embedding, all_chunks, model):
    """
    Get semantic nouns from all chunks at once, then highlight them in individual chunks.
    Much more efficient than processing each chunk separately.
    
    Parameters:
    - query: the search query string
    - query_embedding: the query embedding
    - all_chunks: list of all chunks to process
    - model: the embedding model
    
    Returns:
    - list of chunks with highlighted nouns
    """
    from bs4 import BeautifulSoup
    import re
    
    # Concatenate all chunk texts (keep HTML for highlighting later)
    all_texts = []
    for chunk in all_chunks:
        all_texts.append(chunk['text'])
    
    # Join all texts with a separator
    combined_text = " [SEP] ".join(all_texts)
    
    # Parse HTML once for the combined text
    soup = BeautifulSoup(combined_text, "html.parser")
    combined_clean_text = soup.get_text()
    
    # Get semantic nouns from the combined clean text (single API call)
    with timing('get_semantic_nouns_222'):
        semantic_nouns = get_semantic_nouns_222(query, query_embedding, combined_clean_text, model)
    
    # Highlight nouns in each chunk
    for chunk in all_chunks:
        for noun in semantic_nouns:
            # This regex is designed to skip over HTML tags and only match whole words.
            # It uses a negative lookbehind and lookahead to ensure the noun is not already bold.
            regex = r'(<[^>]*>)|(\b' + re.escape(noun) + r'\b)'

            def repl(m):
                # If the first group (the HTML tag) is present, return it as is.
                if m.group(1):
                    return m.group(1)
                
                # Check if the word is already bolded by looking at the surrounding text.
                # This is a simplified check. For more complex cases, a proper HTML parser would be better.
                # Here we check if the match is inside <b>...</b>
                start, end = m.span(2)
                
                # Check for opening bold tag before the match
                pre_match = chunk['text'][:start]
                # Check for closing bold tag after the match
                post_match = chunk['text'][end:]

                # A simple check for being inside a bold tag. 
                # This might not be perfect for all nested cases but works for many.
                if pre_match.rfind('<b>') > pre_match.rfind('</b>') and post_match.find('</b>') != -1:
                    return m.group(2)
                else:
                    return f'<b>{m.group(2)}</b>'

            chunk['text'] = re.sub(
                regex,
                repl,
                chunk['text'],
                flags=re.IGNORECASE
            )
    
    return all_chunks

def get_nouns(query, text):
    """
    Extract nouns from query that match nouns found in the text.
    
    Parameters:
    - query: the search query string
    - text: the text content to search in
    
    Returns:
    - list of nouns from the query that appear in the text
    """
    from bs4 import BeautifulSoup
    
    # Parse HTML content and extract text
    soup = BeautifulSoup(text, "html.parser")
    text_content = soup.get_text()
    
    # Process query with spaCy to extract nouns
    query_doc = nlp(query)
    query_nouns = [token.text.lower() for token in query_doc 
                   if token.pos_ in ["NOUN", "PROPN"]]
    
    # Process text with spaCy to extract nouns
    text_doc = nlp(text_content)
    text_nouns = set([token.text.lower() for token in text_doc 
                      if token.pos_ in ["NOUN", "PROPN"]])
    
    # Find query nouns that appear in the text
    matching_nouns = []
    for query_noun in query_nouns:
        # Remove special characters for matching
        clean_query_noun = re.sub(r'[^\w\s]', '', query_noun)
        if clean_query_noun in text_nouns:
            matching_nouns.append(query_noun)
    
    return matching_nouns

if __name__ == "__main__":
    # Example usage
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    text = '<table><tbody><tr><th>Patient characteristic</th><th>Patients willing to use VR (n=30)</th><th>Patients unwilling to use VR (n=57)</th></tr><tr><td>Age (years), mean (SD)</td><td>49.7 (17.4)</td><td>60.2 (17.7)</td></tr><tr><td>Sex (male), n (%)</td><td>19 (63)</td><td>28 (49)</td></tr><tr><td>Race/Ethnicity, n (%)a</td><td></td><td></td></tr><tr><td>Non-Hispanic white</td><td>25 (83)</td><td>29 (66)</td></tr><tr><td>Black</td><td>3 (10)</td><td>9 (20)</td></tr><tr><td>Asian</td><td>1 (3)</td><td>1 (2)</td></tr><tr><td>Hispanic white</td><td>1 (3)</td><td>4 (9)</td></tr><tr><td>Other</td><td>0</td><td>1 (2)</td></tr><tr><td>Reason for hospitalization, n (%)</td><td></td><td></td></tr><tr><td>Gastrointestinal</td><td>9 (30)</td><td>22 (39)</td></tr><tr><td>Cardiac</td><td>3 (10)</td><td>7 (12)</td></tr><tr><td>Pain control</td><td>3 (10)</td><td>1 (2)</td></tr><tr><td>Infectious disease</td><td>8 (27)</td><td>7 (12)</td></tr><tr><td>Hematological/Oncological</td><td>2 (7)</td><td>7 (12)</td></tr><tr><td>Neurological</td><td>1 (3)</td><td>1 (2)</td></tr><tr><td>Pulmonary</td><td>1 (3)</td><td>2 (4)</td></tr><tr><td>Rheumatologic</td><td>1 (3)</td><td>1 (2)</td></tr><tr><td>Other</td><td>2 (7)</td><td>9 (16)</td></tr></tbody></table>'
    query = "patients with cardiac disease"
    
    # Test get_semantic_nouns (similarity-based)
    query_embedding = get_query_embedding(query, model)
    print("Semantic nouns:", get_semantic_nouns(query, query_embedding, text, model))
    
    # Test get_nouns (exact noun matching)
    print("Matching nouns:", get_nouns(query, text))
