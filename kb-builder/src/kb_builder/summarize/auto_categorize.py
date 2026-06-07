import io
import requests

import google.generativeai as genai


from kb_builder.persistence.document_sqlite import get_categories, get_category_summaries, insert_category
from kb_builder.hparams_config import hpc

from shared.config import Config
from shared.logger import Logger
from shared.call_llm_api import retry_generate_until_success
from shared.embedding.sentence_transformer import sentence_transformer_model
from kb_builder.db_support.category_db_file_paths import dbs

def summarize_txt(txt):
    genai.configure()
    model = genai.GenerativeModel(hpc().GEMINI_MODEL)
    prompt = "Summarize this text in 100 words or less: " + txt
    response = model.generate_content(prompt)
    return response.text

def summarize_categories():
    # get the set of categories in the CATEGORY column of the documents table
    print("Summarizing categories")
    categories = get_categories()   

    # configure the generative model and the embedding model
    embedding_model = sentence_transformer_model()

    cat_vec_db = dbs.category_vectors

    # then for each category get the set of documents with that document category
    for category in categories:
        category = category[0]
        Logger.info("Summarizing category: " + category)    
        
        documents = get_category_summaries(category)
        
        if len(documents) == 0:
            continue
        
        prompt = io.StringIO()
        prompt.write(f"Using 100 words or less, summarize what this category represents. The category is '{category}'. Here are the documents in this category:\n\n")
        for document in documents:
            prompt.write(f"Document: {document[0]}\nSummary: {document[1]}\n\n")
        
        prompt = prompt.getvalue()
        
        import litellm
        response = litellm.completion_with_retries(model=hpc().categorize.summary_model[len('litellm/'):], 
                                            messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        Logger.info("Summarized category: " + category )
        
        category_id = insert_category(category, response)
        category_embedding = embedding_model.embed_many([response])[0]
        cat_vec_db.add_items([category_embedding], [category_id])
