import nltk
import inflect
import os

# Pre-Download the required NLTK data from terminal:
# poetry run python -m nltk.downloader -d ~/.nltk_data punkt averaged_perceptron_tagger wordnet

# Set up NLTK data path
nltk_data_dir = os.path.expanduser('~/.nltk_data') # Set the path to the NLTK data directory
nltk.data.path.append(nltk_data_dir) # Add the NLTK data directory to the list of paths

# Create an instance of the inflect engine
p = inflect.engine()

#depracated replaced with semantic_nouns.py
def getNouns(text):
    nlkt_resource = 'averaged_perceptron_tagger_eng'
    # check if nltk already has the resource
    nltk.download(nlkt_resource)

    # Tokenize the text
    tokens = nltk.word_tokenize(text)

    # Perform part-of-speech tagging
    tagged = nltk.pos_tag(tokens)

    # Extract nouns and get their singular/plural forms
    nouns = []
    lemmatizer = nltk.stem.WordNetLemmatizer()
    for word, pos in tagged:
        if pos.startswith('NN'):  # Check if the tag starts with 'NN' (noun)
            singular = lemmatizer.lemmatize(word, 'n')
            plural = p.plural(singular)

            lower = plural.lower()
            nouns.append(lower)
            nouns.append(plural.upper())
            nouns.append(lower[0].upper() + lower[1:])

            lower = singular.lower()
            nouns.append(lower)
            nouns.append(singular.upper())
            nouns.append(lower[0].upper() + lower[1:])

    # Filter out non-noun words
    nouns = [word for word in nouns if word.lower() not in [token.lower() for token in tokens if not nltk.pos_tag([token])[0][1].startswith('NN')]]
    # print(f'*** My Nouns: {nouns}')
    return nouns
