from typing import *
import torch
from transformers import AutoTokenizer, AutoModel
from shared.logger import Logger
from shared.config import cfg
from shared.hparams_config import hpc

max_seq_lengths = {
    'sentence-transformers/all-MiniLM-L6-v2': 128,
    'nvidia/NV-Embed-v2': 32768
}


# Define task and data
task_name_to_instruct = {"example": "Given a question, retrieve passages that answer the question"}
query_prefix = "Instruct: " + task_name_to_instruct["example"] + "\nQuery: "

class JointSentenceEmbedder:

    def __init__(self, model):
        # Load model and tokenizer
        self.model_name = model
        self.model = AutoModel.from_pretrained(model, trust_remote_code=True)
        if hasattr(self.model, 'tokenizer'):
            self.tokenizer = self.model.tokenizer
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)

    def emb_toks(self, toks:torch.Tensor, task='nvidia/NV-Embed-v2text-matching') -> torch.Tensor:
        model_args = {
            'input_ids': toks,
            'attention_mask': torch.ones(toks.shape, dtype=torch.long)
        }
        is_jina_v3 = (self.model_name == 'jinaai/jina-embeddings-v3')
        if is_jina_v3:
            task_id = self.model._adaptation_map[task]
            adapter_mask = torch.full((len(toks),), task_id, dtype=torch.int32)
            model_args['adapter_mask'] = adapter_mask
        with torch.no_grad():
            outputs = self.model(**model_args)
            # Get the last hidden state (token embeddings before pooling)
            if 'sentence_embeddings' in outputs:
                token_embeddings = outputs['sentence_embeddings']# Shape: [batch_size, seq_length, hidden_dim]
            elif 'last_hidden_state' in outputs:
                token_embeddings = outputs['last_hidden_state']

        if not isinstance(token_embeddings, torch.Tensor):
            return torch.tensor(token_embeddings)
        else:
            return token_embeddings

    def emb_each_sentence(self, sentences: List[str]):
        """
        each sentence is represented by tensor of token ids
        each sentence should not have eos token at the end
        """
        if self.model_name == 'jinaai/jina-embeddings-v3':
            sentences = [
                self.model._task_instructions['retrieval.passage'] + sentence
                for sentence in sentences
            ]
        try:
            chunks = self.tokenize_each(sentences)
        except Exception as e:
            print('error', type(e), e)
            raise e
        sentence_embs = []
        cls_tok = torch.tensor([self.tokenizer.cls_token_id])
        sep_tok = torch.tensor([self.tokenizer.sep_token_id])
        is_jina = self.model_name.startswith('jinaai')
        for chunk in chunks:
            if is_jina:
                joined = torch.cat([cls_tok] + chunk + [sep_tok])
            else:
                joined = torch.cat(chunk)
            print("running on ", joined.shape, self.tokenizer.decode(joined))
            token_embeddings = self.emb_toks(torch.unsqueeze(joined, 0), 'retrieval.passage')[0]
            if is_jina:
                token_embeddings = token_embeddings[1:-1]

            tok_i = 0
            for sentence in chunk:
                # Average token embeddings for each sentence
                sentence_embs.append(token_embeddings[tok_i:tok_i + len(sentence)].mean(dim=0).cpu())
                tok_i += len(sentence)


        return torch.stack(sentence_embs, dim=0)

    def tokenize_each(self, texts) -> List[List[torch.Tensor]]:
        toks = [self.tokenize([x])['input_ids'][0] for x in texts]
        max_len = hpc().MAX_TOKENS_IN_CHUNK
        chunks = [[]]
        ntoks = 0
        for sentence_toks in toks:
            assert len(sentence_toks) < max_len, f"Tokenized sentence too long: {len(sentence_toks)}"
            ntoks += len(sentence_toks)
            if ntoks >= max_len:
                chunks.append([sentence_toks])
                ntoks = len(sentence_toks)
            else:
                chunks[-1].append(sentence_toks)
        print("got n chunks", len(chunks))
        return chunks

    def tokenize(self, txts: List[str], add_special_tokens=False):
        """
        Apply the tokenizer to a list of text strings.
        Ensures truncation/padding to a maximum length.
        """
        max_length = hpc().MAX_TOKENS_IN_CHUNK

        # Optional check that each text < max_length chars (depending on your usage)
        # but realistically you'd want to check token length rather than char length.
        # for txt in txts:
        #     assert len(txt) < max_length, f"sentence too long: {len(txt)}"

        # Tokenize with truncation/padding
        encoded = self.tokenizer(
            txts,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=max_length - 1,
            add_special_tokens=add_special_tokens
        )
        if encoded['input_ids'].shape[1] == 0 and encoded['input_ids'].dtype == torch.float32:
            encoded['input_ids'] = encoded['input_ids'].to(torch.int64)
        print("toks shape", encoded['input_ids'].shape, encoded['input_ids'].dtype)
        return encoded

    def strs_to_toks_with_instruct(self, queries: List[str]):
        txts = queries
        return self.tokenize(txts, add_special_tokens=self.model_name.startswith('jinaai/jina-embeddings-v2'))['input_ids']


    def emb_strs(self, txts: List[str]):
        if self.model_name == 'jinaai/jina-embeddings-v3':
            txts = [
                self.model._task_instructions['retrieval.query'] + txt
                for txt in txts
            ]
        toks = self.strs_to_toks_with_instruct(txts)
        # emb_toks outputs [batch_size, seq_length, hidden_dim], so we mean across seq_length
        return self.emb_toks(toks, 'retrieval.query').mean(dim=1).cpu()

    def emb_query(self, query):
        return self.emb_strs([query])[0]

    def get_tokenizer(self):
        return self.tokenizer

#    def relevant_sentences_within_doc(sentence_i: int, sentences: List[torch.Tensor]):
        # 


