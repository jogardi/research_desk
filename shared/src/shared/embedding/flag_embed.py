from typing import List
import torch
from FlagEmbedding import BGEM3FlagModel
from shared.logger import Logger
from shared.config import cfg
from shared.hparams_config import hpc

class FlagMultiVecEmbedder:
    """
    A class for embedding text using the multi-vector (ColBERT) mode of the BGE-M3 FlagEmbedding model.
    
    This approach returns multiple vectors per text, which is useful for multi-vector retrieval.
    """
    def __init__(self, model_name):
        """
        Initialize the FlagMultiVecEmbedder.

        Parameters:
            model_name (str): The identifier for the BGE-M3 model.
            use_fp16 (bool): Whether to use half-precision for faster computation.
        """
        self.model_name = model_name
        self.model = BGEM3FlagModel(model_name, use_fp16=True)
        self.tokenizer = self.model.tokenizer

    def emb_each_sentence(self, sentences: List[str]):
        import numpy as np
        # the tokenizer adds eos and bos and bos is dropped in https://github.com/FlagOpen/FlagEmbedding/blob/fcdf889ec91edcd5278ba33a08c0665f4a59feb6/FlagEmbedding/finetune/embedder/encoder_only/m3/modeling.py#L150
        if len(sentences) == 1 and len(sentences[0]) == 0:
            print("empty sentence", sentences)
            return np.zeros((1, 768))
        output = self.emb_strs([''.join(sentences)])[0]
        embs = []
        tok_i = 0
        n_toks_so_far = 0
        did_encounter_empty_part = False
        for sentence_i, sentence in enumerate(sentences):
            # ntoks = self.tokenizer(sentence, return_tensors="pt", add_special_tokens=False)['input_ids'].shape[1]
            ntoks = self.tokenizer(''.join(sentences[:sentence_i+1]), return_tensors="pt", add_special_tokens=False)['input_ids'].shape[1]
            part = output[n_toks_so_far:ntoks]
            if len(part) == 0:
                print("empty part", sentence, ntoks, tok_i)
                did_encounter_empty_part = True
            embs.append(np.mean(part, axis=0))
            print("processed sentence", sentence_i, sentence)
            # check no nan in embs
            # assert not np.isnan(embs[-1]).any(), f"nan in emb for sentence {sentence}"
            n_toks_so_far = ntoks

        if did_encounter_empty_part:
            print("output", output.shape, len(sentences), tok_i)
        if len(embs) == 0:
            print("empty embs", embs.shape, sentences)

        return np.vstack(embs)

        # import numpy as np
        # return [

        #     np.mean(vec, axis=0)
        #     for vec in output
        # ]

    def emb_strs(self, texts: List[str], max_length: int = 8192, batch_size: int = 12, is_query: bool = False) -> List[torch.Tensor]:
        """
        Generate multi-vector (ColBERT) embeddings for a list of texts.
        
        Each text is represented as a tensor containing multiple vectors (i.e. one per token or sub-piece
        as determined by the model's internal mechanism). These vectors can later be used for fine-grained 
        multi-vector matching.
        
        Parameters:
            texts (List[str]): A list of input text strings.
            max_length (int): The maximum token length to use during encoding.
            batch_size (int): Batch size for the encoding process.
        
        Returns:
            List[torch.Tensor]: A list where each element is a tensor of multi-vector embeddings
                                corresponding to one input text.
        """
        args = dict()
        f = self.model.encode
        if is_query:
            f = self.model.encode_queries
            # args['instruction'] = "Represent this sentence for searching relevant passages:"
            # args['instruction_format'] = "{}{}"
        output = f(
            texts,
            batch_size=batch_size,
            max_length=max_length,
            return_dense=False,
            return_sparse=False,
            return_colbert_vecs=True,
            **args
        )
        # The returned dictionary should contain colbert_vecs as a list, one per input text.
        return output["colbert_vecs"]

    def emb_query(self, query: str, max_length: int = 8192, batch_size: int = 12) -> torch.Tensor:
        """
        Generate a multi-vector embedding for a single query.

        Parameters:
            query (str): The input query string.
            max_length (int): The maximum token length to use during encoding.
            batch_size (int): Batch size for the encoding process.
            
        Returns:
            torch.Tensor: A tensor containing the multi-vector embedding for the query.
        """
        import numpy as np
        colbert_vecs = self.emb_strs([query], max_length=max_length, batch_size=batch_size, is_query=True)
        return np.mean(colbert_vecs[0], axis=0)

    def tokenize(self, texts: List[str], add_special_tokens: bool = True):
        """
        Tokenize a list of text strings using the model's tokenizer.
        
        Parameters:
            texts (List[str]): List of texts to be tokenized.
            add_special_tokens (bool): Whether to add special tokens.
            
        Returns:
            A dictionary containing the tokenized outputs (e.g., input_ids, attention_mask).
        """
        max_length = hpc().MAX_TOKENS_IN_CHUNK
        encoded = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=max_length,
            add_special_tokens=add_special_tokens,
        )
        return encoded

    def get_tokenizer(self):
        return self.tokenizer