import re
import inflect

# Common English stop words
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'or', 'that',
    'the', 'to', 'was', 'will', 'with', 'what', 'when', 'where', 
    'which', 'who', 'why', 'how', 'this', 'these', 'those', 'have',
    'had', 'do', 'does', 'did', 'can', 'could', 'should', 'would',
    'may', 'might', 'must', 'shall', 'will', 'am', 'is', 'are',
    'was', 'were', 'been', 'being', 'have', 'has', 'had', 'having'
}

def getKeywords(text, is_fts=True):
    text = text.lower() # Convert the text to lowercase
    text = text.replace('"', '') # remove double quotes
    text = re.sub(r'near\(\w+ \w+, \d+\)', '', text) # remove any pattern: "near(word1 word2, a-number)"
    
    # Split into words and filter out stop words
    words = text.lower().split()
    keywords = [word for word in words if word not in STOP_WORDS]
    
    # Initialize inflect engine
    p = inflect.engine()
    
    # Create a set to store all variations (original, singular, plural, uppercase, capitalized)
    all_variations = []
    def add_if_no_in(x):
        if x not in all_variations:
            all_variations.append(x)
    
    for word in keywords:
        if is_fts:
            plural = p.plural_noun(word) or word
            singular = p.singular_noun(word) or word
            for x in [plural, word, singular]:
                add_if_no_in(x)
                add_if_no_in(x.upper())
                add_if_no_in(x.capitalize())
        else:
            add_if_no_in(word)

    
    return all_variations