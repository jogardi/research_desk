import os
import traceback
import numpy as np
from shared.config import Config
from shared.sqlite import SQLite
from kb_builder.hparams_config import hpc
from shared.hparams_config import hpc as shared_hpc
from kb_builder.vectorize.chunk_and_embed import chunk_and_embed
from kb_builder.auto_categorize import summarize_txt

from shared.embedding.sentence_transformer import sentence_transformer_model
from kb_builder.db_support.category_db_file_paths import CategoryDBFilePaths

from kb_builder.persistence.document_sqlite import *
from kb_builder.persistence.category_sqlite import * 
from kb_builder.vectorize.chunker import Chunker

from shared.logger import Logger
from kb_builder.util.log_util import log_processing_warning, log_processing_error 
from kb_builder.pre_processor.pdf_block import PDFBlock
from kb_builder.pre_processor.video_block import VideoBlock
from typing import Union

if 'kb-builder' in os.getcwd():
    from kb_builder.vector_db.hnswlib import HnswlibVectorDB
else:
    from vector_db.hnswlib import HnswlibVectorDB

def add_document(pdf_blocks, artifact_filename: str, category: str, source: str):
    if (not exists_category_database()):
        create_category_database()

    document = ''.join([pdf_block.text for pdf_block in pdf_blocks])
    # Insert the file name into the DOCUMENT table
    # Read the document text and Split into chunks
    # collect the chunk into all_chunks list
    # Insert the chunks into the CHUNK table and collect the chunk IDs
    summary = summarize_txt(document[:2_000])
    
    # Extract publication date from the document blocks
    from kb_builder.util.publication_date_extractor import extract_publication_date_from_blocks
    publication_date = extract_publication_date_from_blocks(pdf_blocks, artifact_filename)
        
    return insert_document(artifact_filename, category, source, summary, publication_date)


def process(block: Union[PDFBlock, VideoBlock], artifact_filename: str, category: str, document_id) -> bool:
    document = block.text
    if len(document.strip()) == 0:
        return True
    import json
    embedding_model = sentence_transformer_model()
    dim = embedding_model.dim()
    assert dim is not None
    
    # Handle serialization for both PDFBlock and VideoBlock
    if hasattr(block.region, 'to_dict'):
        # VideoBlock with to_dict method
        region_json = json.dumps(block.region.to_dict())
    else:
        # PDFBlock - use default serialization
        region_json = json.dumps(block.region, default=lambda o: o.__dict__)

    chunks, embeddings = chunk_and_embed(document, embedding_model, block.type)
    if (Config.TITLING_ENABLED == '1'):
        from kb_builder.title.title_generator import TitleGenerator
        title_gen = TitleGenerator(enable_mps=hpc().ENABLE_MPS)

    chunks_with_titles = []
    for chunk in chunks:
        if (Config.TITLING_ENABLED == '0'):
            title = "N/A"
        else:
            title = title_gen.generate_title(chunk)
            if not title:
                title = title_gen.generate_title(chunk, .7)
                if not title:
                    title = title_gen.generate_title(chunk, .9)
                    if not title:
                        title = "N/A"
                        log_processing_warning(artifact_filename, category, "Title could not be generated for chunk")       
        
        if (Config.TITLING_ENABLED == '1'):
            Logger.info(f"Title: {title}")
            
        chunks_with_titles.append({ "chunk": chunk, "title": title })

    # populate chunk table
    sqldb = SQLite(CategoryDBFilePaths.sqlite_file_path) 
    lucene = None
    with sqldb.lock():
        try:
            sqldb.open() 
            sqldb.begin_transaction()
            
            chunk_ids = []
            for chunk in chunks_with_titles:
                id = sqldb.insert("insert into CHUNK (CONTENT, DOCUMENT_ID, TITLE, REGION) values (?, ?, ?, ?)", (chunk['chunk'], document_id, chunk['title'], region_json))
                chunk_ids.append(id)
                
            # populate vector db    
            vector_db = HnswlibVectorDB(CategoryDBFilePaths.hnswlib_file_path, dim) 
            # check no nan in embeddings
            assert not np.isnan(embeddings).any(), "nan in embeddings"
            vector_db.add_items(embeddings, chunk_ids)
            
            sqldb.commit()
            
            return True

        except Exception as e:  
            sqldb.rollback()   
            cleanup_document(artifact_filename, category)         
            Logger.error_formatted(f"An error occurred while vectorizing {artifact_filename}", e)
            import traceback
            traceback.print_exc()
            return False
        finally: 
            sqldb.close()
            if lucene is not None:
                lucene.close()
        
def cleanup_document(artifact_filename: str, category: str):
    try:
        delete_document(artifact_filename, category)
    except Exception as e:
        Logger.error_formatted(f"An error occurred while deleting document {artifact_filename}", e)

        
    
def add_category_vector(category_id: int, vec):
    db_path = str(Path(Config.DB_FOLDER) / 'vector_db/hnswlib/categories.db')
    vector_db = HnswlibVectorDB(db_path, vec.shape[0])
    vector_db.add_items([vec], [category_id])