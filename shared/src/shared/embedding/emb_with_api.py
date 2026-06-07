from typing import List
from litellm import embedding
from functools import lru_cache
from shared.hparams_config import hpc
from concurrent.futures import ThreadPoolExecutor, as_completed
batch_size_limits = {
    'voyage/voyage-3-large': 20,#128,
}

def retry_ntimes(func, n, delay=1):
    for i in range(n):
        try:
            return func()
        except Exception as e:
            import time
            time.sleep(delay)
    raise Exception(f"Failed after {n} retries")

class EmbWithApi:

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.is_jina = model_name.startswith('jina_ai')

    def emb_query(self, text: str):
        extra_args = dict()
        if self.is_jina:
            extra_args['task'] = 'text-matching'

        data = embedding(input=[text], model=self.model_name, num_retries=10, max_retries=10, **extra_args).data
        import numpy as np
        vec = np.array(data[0]['embedding'])
        # normalize
        return vec / np.linalg.norm(vec)



    def emb_each_sentence(self, texts: List[str]):
        import torch
        extra_args = dict()
        batch_size = batch_size_limits.get(self.model_name, 2048)
        if self.is_jina:
            if hpc().IS_LATE_CHUNKING:
                extra_args['task'] = 'text-matching'
                extra_args['late_chunking'] = True
                batch_size = hpc().LATE_CHUNKING_BATCH_SIZE
            else:
                extra_args['task'] = 'retrieval.passage'
                
        def process_batch(i: int):
            batch = texts[i:i+batch_size]

            try:
                data = embedding(input=batch, model=self.model_name, num_retries=10, max_retries=10, **extra_args).data

                if len(data) == 0:
                    print("no resuls for batch", batch)
            except Exception as e:
                print(f"Error in embedding batch {i} of size {len(batch)}: {batch}")
                for text in batch:
                    assert text is not None
                    assert type(text) == str
                    assert len(text) > 0
                raise e
            return [torch.tensor(x['embedding']) for x in data]
        
        # Process batches in parallel
        batch_indices = range(0, len(texts), batch_size)
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(map(process_batch, batch_indices))
            if len(results) == 0:
                print("no results for all batches", texts)
            xs = []
            for batch_result in results:
                xs.extend(batch_result)
        
        try:
            return torch.stack(xs)
        except RuntimeError as e:
            print("could not stack", xs, results, texts)
            raise e
    
    @lru_cache()
    def get_tokenizer(self):
        from transformers import AutoTokenizer
        if self.is_jina:
            return AutoTokenizer.from_pretrained(self.model_name.replace('jina_ai/', 'jinaai/'))
        elif 'm2-bert' in self.model_name or self.model_name.startswith('voyage'):
            return AutoTokenizer.from_pretrained("bert-base-uncased")
        elif self.model_name == 'together_ai/BAAI/bge-large-en-v1.5':
            return AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")
        else:
            raise ValueError(f"Tokenizer not supported for model {self.model_name}")
