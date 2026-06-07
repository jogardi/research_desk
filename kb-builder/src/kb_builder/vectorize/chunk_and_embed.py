from kb_builder.vectorize.chunker import Chunker
from kb_builder.hparams_config import hpc
from shared.hparams_config import hpc as shared_hpc

def chunk_and_embed(document: str, model, block_type):
    no_chunk_types = shared_hpc().NO_CHUNK_BLOCK_TYPES
    if block_type in no_chunk_types:
        # TODO what happens if it is too big for embedding model
        chunks = [document]
    elif block_type == 'transcript':
        # For video transcripts, always use sentence splitting even if agentic chunking is enabled
        print('using sentence splitting for video transcript')
        from kb_builder.vectorize.chunker import non_agentic_split_text_by_sentence_and_tokens
        chunks = non_agentic_split_text_by_sentence_and_tokens(document, model.get_tokenizer(), shared_hpc().MAX_TOKENS_IN_CHUNK)
    else:
        if hpc().CHUNKING_TYPE == 'sentence':
            # TODO what happens if agnetic hcunking gave chunk too big for embedding model
            chunks = Chunker.split_document_by_sentence(document, hpc().CHUNK_SENTENCE_SIZE, shared_hpc().MAX_TOKENS_IN_CHUNK, model.get_tokenizer())
        else:
            chunks = Chunker.split_document_by_chunk(document, hpc().CHUNK_SIZE, hpc().CHUNK_OVERLAP_SIZE)

    if len(chunks) == 0:
        print("got no chunks", len(document), document)

    embeddings = model.embed_many(chunks)
    import numpy as np
    chunks, embeddings = zip(*[
        (chunk, emb)
        for chunk, emb in zip(chunks, embeddings)
        # check no nan in embeddings
        if not np.isnan(emb).any()
    ])

    return chunks, embeddings
    