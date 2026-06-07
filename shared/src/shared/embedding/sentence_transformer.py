# import sys_path # Add the "ai_pipeline" directory to the sys.path

from shared.embedding._interface import EmbeddingModel
from typing import List
from functools import lru_cache

from shared.config import Config
from shared.config import cfg
from shared.hparams_config import hpc
from functools import lru_cache

class SentenceTransformerModel(EmbeddingModel):

    def __init__(self, model=None) -> None:
        if model is None:
            model = hpc().EMBED_MODEL

        if model.startswith('litellm/'):
            from shared.embedding.emb_with_api import EmbWithApi
            self.embedder = EmbWithApi(model[len('litellm/'):])
        elif model.startswith('multivec_api/'):
            from shared.embedding.multivec_api import MultivecAPI
            self.embedder = MultivecAPI(model[len('multivec_api/'):])
        elif model.startswith('flag/'):
            from shared.embedding.flag_embed import FlagMultiVecEmbedder
            self.embedder = FlagMultiVecEmbedder(model[len('flag/'):])
        else:
            from shared.embedding.joint_emb import JointSentenceEmbedder
            self.embedder = JointSentenceEmbedder(model[len('hug/'):])

    def embed(self, text: str):
        # return self.embedder.model.encode(text, task='retrieval.query')
        # x = torch.tensor(self.embedder.model.encode(text))
        import numpy as np
        x = np.array(self.embedder.emb_query(text))
        # normalize
        return x / np.linalg.norm(x)
        # return torch.nn.functional.normalize(x, p=2, dim=0)

    def embed_many(self, texts: List[str]):
        # return self.embedder.model.encode(texts, task='retrieval.passage')
        # x = torch.tensor(self.embedder.model.encode(texts))
        x = self.embedder.emb_each_sentence(texts)
        # check if x is a numpy array
        if str(type(x)) == "<class 'numpy.ndarray'>":
            import numpy as np
            # normalize each row
            return x / np.linalg.norm(x, axis=1, keepdims=True)
        else:
            import torch
            # normalize each row
            return torch.nn.functional.normalize(x, p=2, dim=1)

    @lru_cache()
    def dim(self) -> int:
        return len(self.embed('hello world'))

    def get_tokenizer(self):
        return self.embedder.get_tokenizer()

@lru_cache()
def sentence_transformer_model():
    return SentenceTransformerModel()
