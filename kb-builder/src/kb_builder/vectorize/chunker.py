import nltk
from functools import lru_cache
from nltk.tokenize import sent_tokenize
import re
from kb_builder.hparams_config import hpc

from shared.logger import Logger

def naive_sentence_split(text):
    import io
    # Define a regex pattern for sentence boundaries
    # Match sentence-ending punctuation (., ?, !) followed by whitespace or end of string
    pattern = r'([\.!?]|\n{2,})\s*'
    out = []
    idx = 0
    for match in re.finditer(pattern, text):
        out.append(text[idx:match.end()])
        idx = match.end()
    out.append(text[idx:])
    return out

def spacy_sentence_split(text):
    import spacy
    # download spacy model if not already downloaded
    if not spacy.util.is_package("en_core_web_sm"):
        spacy.cli.download("en_core_web_sm")
    spacy.require_gpu()
    nlp = spacy.load("en_core_web_sm", enable=["sentencizer"])
    # nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    doc = nlp(text)
    sentences_txts = []
    spacy_sents = list(doc.sents)
    if len(spacy_sents) == 0:
        if len(text) == 0:
            return []
        else:
            return [text]

    return [s.text_with_ws for s in spacy_sents]
    # for sent, next_sent in zip(spacy_sents[:-1], spacy_sents[1:]):
    #     sentences_txts.append(text[sent.start_char:next_sent.start_char])
    # sentences_txts.append(text[spacy_sents[-1].start_char:])
@lru_cache()
def sat_model():
    from wtpsplit import SaT
    return SaT("sat-3l")

def sat_3l_split(text):
    sat = sat_model()
    return sat.split(text)


def get_token_encoding(text: str, tokenizer):
    return tokenizer.encode_plus(
        text,
        add_special_tokens=False,
        return_offsets_mapping=True
    )

def chunk_by_max_tokens(text, tokenizer, max_tokens=512, merge_threshold=None):
    """
    Given a text string, break it into sub-chunks so that each sub-chunk has at most
    `max_tokens` tokens according to the Hugging Face tokenizer, while preserving all whitespace.
    
    If merge_threshold is provided (and > 0), then after initial chunking the function will
    attempt to merge any two adjacent chunks whose combined token count is less than merge_threshold.
    The merging is done iteratively starting with the pairs with the smallest combined token count.
    
    Returns a list of exact substrings that when joined equal the original text.
    """
    # Handle empty or whitespace-only text
    if len(text) == 0:
        return []

    # Get token offsets for the entire text
    encoding = get_token_encoding(text, tokenizer)
    offsets = encoding["offset_mapping"]
    
    # Split into chunks based on token count
    chunks = []
    current_start = 0
    current_tokens = 0
    
    for i, (start, end) in enumerate(offsets):
        current_tokens += 1
        
        # When we hit max tokens, create a chunk (including the current token)
        if current_tokens >= max_tokens:
            chunk = text[current_start:end]
            chunks.append(chunk)
            
            # Reset for the next chunk
            current_start = end
            current_tokens = 0
    
    # Add any remaining text as the final chunk
    if current_start < len(text):
        chunks.append(text[current_start:])
    
    # If merge_threshold is not provided or less than or equal to 0, no merging is performed.
    if merge_threshold is None or merge_threshold <= 0:
        return chunks

    # Compute token counts for each chunk using the tokenizer's offset mapping.
    token_counts = [len(get_token_encoding(chunk, tokenizer)["offset_mapping"]) for chunk in chunks]

    # Iteratively merge adjacent chunks whose combined token count is below merge_threshold.
    # At each iteration, merge the adjacent pair with the smallest combined token count.
    merged = True
    while merged:
        merged = False
        best_index = None
        best_sum = None

        # Look for the adjacent pair with the smallest sum of token counts that qualifies for merging.
        for i in range(len(chunks) - 1):
            combined = token_counts[i] + token_counts[i+1]
            if combined < merge_threshold:
                if best_sum is None or combined < best_sum:
                    best_sum = combined
                    best_index = i
        
        # If a candidate pair was found, merge it.
        if best_index is not None:
            # Merge the two chunks
            new_chunk = chunks[best_index] + chunks[best_index+1]
            new_token_count = len(get_token_encoding(new_chunk, tokenizer)["offset_mapping"])

            # Replace the two chunks with the merged chunk in both lists.
            chunks = chunks[:best_index] + [new_chunk] + chunks[best_index+2:]
            token_counts = token_counts[:best_index] + [new_token_count] + token_counts[best_index+2:]
            merged = True

    return chunks

def split_text_by_sentence_and_tokens(text, tokenizer, max_tokens=512):
    """
    1) Split text into sentences using naive_sentence_split
    2) For each sentence, further split by token count if needed
    3) Preserve all whitespace and ensure chunks join back to original text
    """
    # Handle empty text
    if len(text) == 0:
        return []
    
    # Check if agentic chunking is enabled
    if hpc().enable_agentic_chunking:
        # When agentic chunking is enabled, the text should already have chunk delimiters
        # Split by the special Unicode character. We support both emoji and non-emoji versions.
        chunks = re.split('✂️|✂', text)
        # Filter out empty chunks and strip whitespace
        chunks = [chunk for chunk in chunks if chunk.strip()]
        return chunks
    else:
        return non_agentic_split_text_by_sentence_and_tokens(text, tokenizer, max_tokens)
        

def non_agentic_split_text_by_sentence_and_tokens(text, tokenizer, max_tokens=512):
        
    # First split into sentences
    if hpc().sentence_splitter == 'nltk':
        sentences = sent_tokenize(text)
    elif hpc().sentence_splitter == 'spacy':
        sentences = spacy_sentence_split(text)
    elif hpc().sentence_splitter == 'sat-3l':
        sentences = sat_3l_split(text)
    elif hpc().sentence_splitter == 'naive':
        sentences = naive_sentence_split(text)
    else:
        raise ValueError(f"Unknown sentence splitter: {hpc().sentence_splitter}")
    new_sentences = []
    for r in sentences:
        import re
        # split on . followed by a number like ".1" or ".57"
        pattern = re.compile(r'\.\d+')
        # split on this pattern. The part that the pattern matches should be included at the end of the chunk
        # Find all matches of the pattern
        matches = list(pattern.finditer(r))
        if not matches:
            new_sentences.append(r)
            continue
            
        # Process each match
        last_end = 0
        for match in matches:
            # Get the match position
            match_start = match.start()
            match_end = match.end()
            
            # Add the text before the match plus the match itself
            if match_start > last_end:
                new_sentences.append(r[last_end:match_end])
                last_end = match_end
        
        # Add any remaining text after the last match
        if last_end < len(r):
            if len(new_sentences) == 0:
                new_sentences.append(r[last_end:])
            else:
                new_sentences[-1] = new_sentences[-1] + r[last_end:]
    sentences = new_sentences
    
    # Then split each sentence by tokens if needed
    chunks = []
    for sentence in sentences:
        sentence_chunks = chunk_by_max_tokens(sentence, tokenizer, max_tokens, hpc().merge_threshold)
        chunks.extend(sentence_chunks)
    
    return chunks


class Chunker:
    
     
    # '''
    #     Chunker class for splitting documents into chunks using specified strategy
    # '''
    # @staticmethod
    # def load_pdf(path: str) -> list[str]:
    #     '''
    #         Load a PDF file and return its text
    #     '''
    #     loader = PyPDFLoader(path)
    #     pages = loader.load()
    #     return pages

    @staticmethod    
    def split_document_by_sentence(document: str, sentences_per_chunk: int, max_tokens: int, tokenizer) -> list[str]:
        sentences = split_text_by_sentence_and_tokens(document, tokenizer, max_tokens)
        chunks = [''.join(sentences[i:i + sentences_per_chunk]) for i in range(0, len(sentences), sentences_per_chunk)]
        return chunks

    @staticmethod
    def split_document_by_chunk(document, chunk_size, chunk_overlap) -> list[str]:
        Logger.info(f"Splitting document into chunks of {chunk_size} characters with {chunk_overlap} overlap")
        from langchain.text_splitter import RecursiveCharacterTextSplitter 

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = text_splitter.split_text(document)
        return chunks

    #
    # NOTE: The following methods are not used in the current implementation
    #
    # @staticmethod
    # def split_document_strategy(documents, strategy, chunk_size, chunk_overlap) -> list[str]:
    #     '''
    #         Split a document into chunks of specified size and overlap.
    #     '''
    #     if strategy == 'size':
    #         return Chunker.split_document(documents, chunk_size, chunk_overlap)
    #     elif strategy == 'paragraphs':
    #         return Chunker.split_document_paragraphs(documents, chunk_size, chunk_overlap)
    #     else:
    #         raise ValueError(f"Unknown chunking strategy: {strategy}")
        
    # @staticmethod
    # def split_document_paragraphs(documents, chunk_size, chunk_overlap) -> list[str]:
    #     '''
    #     Split document into paragraphs, and further chunk them if they exceed a specified length.
    #     Prepend overlap to paragraphs or chunks whenever possible.
    #     '''
    #     def split_into_chunks(para, max_length, overlap):
    #         chunks = []
    #         start = 0
    #         while start < len(para):
    #             end = min(start + max_length, len(para))
    #             chunks.append(para[start:end])
    #             # Ensure start always moves forward
    #             start = max(start + max_length - overlap, end)
    #         return chunks

    #     result = []
    #     previous_chunk_end = ""
    #     for document in documents:
    #         # paragraphs = document.page_content.split('\n\n')
    #         paragraphs = re.split(r"\n\s*\n", document.page_content)
    #         for para in paragraphs:
    #             # Prepend overlap from the previous chunk if available
    #             # prepended_para = previous_chunk_end + para
    #             prepended_para = para

    #             # if len(prepended_para) <= chunk_size:
    #             result.append(prepended_para)
    #             # Update the previous_chunk_end for next iteration
    #             previous_chunk_end = prepended_para[-chunk_overlap:]
    #             # else:
    #                 # chunks = split_into_chunks(prepended_para, chunk_size, chunk_overlap)
    #                 # result.extend(chunks)
    #                 # # Update the previous_chunk_end from the last chunk
    #                 # previous_chunk_end = chunks[-1][-chunk_overlap:]

    #     return result


if __name__ == '__main__':
    sample_text = "This is a sample document. It is only used for a local chunking smoke test."
    chunker = Chunker()
    print(chunker.split_document(sample_text, 5))
