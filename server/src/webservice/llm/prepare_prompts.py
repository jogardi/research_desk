import io
from webservice.excerpts.db_operations import generate_excerpt_hash, store_excerpt

def document_to_text(document) -> str:
    chunks = document['chunks']
    with_elipses = io.StringIO()
    with_elipses.write(chunks[0]['text'])
    prev_id = chunks[0]['id']
    for chunk in chunks[1:]:
        if chunk['id'] - prev_id == 1:
            with_elipses.write(chunk['text'])
        else:
            assert chunk['id'] - prev_id > 1
            prev_id = chunk['id']
            with_elipses.write(f"...{chunk['text']}")
    return f"Document name: {document['documentName']} Document: {with_elipses.getvalue()}"


def document_to_text_with_page_numbers(document, kb_name: str) -> str:
    chunks = document['chunks']
    excerpts = document.get('excerpts', [[0, len(chunks) - 1]])  # Default to single excerpt if none specified
    document_id = document['documentID']
    
    with_elipses = io.StringIO()
    with_elipses.write(f"Document: {document['documentCategory']}/{document['documentName']}\n\n")
    
    # Process each excerpt separately
    for excerpt_idx, (start_idx, end_idx) in enumerate(excerpts):
        # Get chunks for this excerpt
        excerpt_chunks = chunks[start_idx:end_idx + 1]
        
        # Generate hash for this excerpt
        chunk_ids = [chunk['id'] for chunk in excerpt_chunks]
        excerpt_hash = generate_excerpt_hash(document_id, chunk_ids)
        
        # Store excerpt in database
        try:
            store_excerpt(document_id, chunk_ids, kb_name, excerpt_hash)
            print(f"Stored search result excerpt {excerpt_hash} for document {document_id}")
        except Exception as e:
            print(f"Warning: Could not store excerpt {excerpt_hash}: {e}")
        
        # Add excerpt header with hash
        if len(excerpts) > 1:
            with_elipses.write(f"\n[Excerpt {excerpt_hash}]\n")
        else:
            with_elipses.write(f"[Excerpt {excerpt_hash}]\n")
        
        # Process chunks within this excerpt
        if excerpt_chunks:
            page_number = excerpt_chunks[0]['region']['page_number']
            with_elipses.write(f"Page {page_number}:\n")
            with_elipses.write(excerpt_chunks[0]['text'])
            prev_id = excerpt_chunks[0]['id']
            
            for chunk in excerpt_chunks[1:]:
                cur_page = chunk['region']['page_number']
                is_same_page = cur_page == page_number
                if not is_same_page:
                    with_elipses.write(f"\nPage {cur_page}:\n")
                    page_number = cur_page
                if chunk['id'] - prev_id == 1 or not is_same_page:
                    with_elipses.write(chunk['text'])
                else:
                    assert chunk['id'] - prev_id > 1
                    prev_id = chunk['id']
                    with_elipses.write(f"...{chunk['text']}")
                prev_id = chunk['id']
        
        # Add spacing between excerpts
        if excerpt_idx < len(excerpts) - 1:
            with_elipses.write("\n\n")
    
    return f"{with_elipses.getvalue()}"
