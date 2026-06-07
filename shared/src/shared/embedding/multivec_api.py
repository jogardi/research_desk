from typing import List
from functools import lru_cache
from shared.hparams_config import hpc

def jina_multi_vector(model_name: str, input_type: str, txts: List[str]):
    import os
    import requests
    url = 'https://api.jina.ai/v1/multi-vector'
    api_key = os.getenv('JINA_AI_API_KEY')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        "model": model_name,
        "dimensions": 128,
        "input_type": input_type,
        "embedding_type": "float",
        "input": txts
    }
    response = requests.post(url, headers=headers, json=data)
    obj = response.json()
    if 'data' not in obj:
        raise Exception(f"Error from jina api: {obj}")
    return [x['embeddings'] for x in obj['data']]

class MultivecAPI:

    def __init__(self, model_name: str):
        if model_name.startswith('jina_ai/'):
            self.model_name = model_name[len('jina_ai/'):]

    def emb_each_sentence(self, texts: List[str]):
        import numpy as np
        batch_size = hpc().LATE_CHUNKING_BATCH_SIZE
        vecs = jina_multi_vector(self.model_name, 'document', texts)
        pooled = np.vstack([
            np.mean(np.array(v), axis=0)
            for v in vecs
        ])
        return pooled

    def emb_query(self, text: str):
        import numpy as np
        vecs = jina_multi_vector(self.model_name, 'query', [text])[0]
        return np.mean(np.array(vecs), axis=0)

    @lru_cache()
    def get_tokenizer(self):
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained('jinaai/jina-colbert-v2')