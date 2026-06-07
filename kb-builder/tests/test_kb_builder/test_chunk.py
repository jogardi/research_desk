import unittest
from transformers import AutoTokenizer
from kb_builder.vectorize.chunker import (
    naive_sentence_split,
    chunk_by_max_tokens,
    split_text_by_sentence_and_tokens,
)
from kb_builder.hparams_config import hpc
hpc().sentence_splitter = 'spacy'


class TestTextSplit(unittest.TestCase):
    # Shared test texts
    TEST_TEXTS = [
        "Hello world! This is a test?Another test.  Last chunk",
        "ThisHasNoPunctuation",
        "",  # Empty string
        "Sentence one.  Sentence two!   ",  # Trailing whitespace
        "Hello " + "X" * 100 + "\nThis is a test",  # Long repeating text
        "AAA " + ("B " * 300),  # Very large chunk
        "Hello world! This is a test. And here's another?\n" + "X" * 900 + " End!",  # Mixed content with large chunk
        " ".join(["word"] * 200)  # 200 repeated words
    ]

    @classmethod
    def setUpClass(cls):
        """
        Runs once for the entire test class. Initializes the Hugging Face tokenizer.
        """
        cls.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    def test_naive_sentence_split_round_trip(self):
        """
        Test that naive_sentence_split preserves the original text when re-joined.
        """
        for text in self.TEST_TEXTS:
            with self.subTest(text=text):
                chunks = naive_sentence_split(text)
                rejoined = "".join(chunks)
                self.assertEqual(rejoined, text, f"Re-joined text does not match the original for: {text}")

    def test_naive_sentence_split_edge_cases(self):
        """
        Check splitting edge cases: no punctuation, blank text, trailing whitespace.
        """
        for text in self.TEST_TEXTS:
            with self.subTest(text=text):
                chunks = naive_sentence_split(text)
                
                # Test round-trip preservation
                self.assertEqual("".join(chunks), text)
                

    def test_chunk_by_max_tokens_round_trip(self):
        """
        Test that chunk_by_max_tokens preserves the original text for chunks of data.
        """
        for text in self.TEST_TEXTS:
            with self.subTest(text=text):
                chunks = chunk_by_max_tokens(text, self.tokenizer, max_tokens=10)
                rejoined = "".join(chunks)
                self.assertEqual(rejoined, text, f"Re-joined text does not match after token-based splitting for: {text}")

    def test_chunk_by_max_tokens_length(self):
        """
        Verify that none of the returned chunks exceed `max_tokens` according to the tokenizer.
        """
        max_tokens = 20
        for text in self.TEST_TEXTS:
            with self.subTest(text=text):
                chunks = chunk_by_max_tokens(text, self.tokenizer, max_tokens=max_tokens)
                
                for c in chunks:
                    tokens = self.tokenizer.encode(c, add_special_tokens=False)
                    self.assertLessEqual(
                        len(tokens), 
                        max_tokens, 
                        f"Chunk exceeds max token limit for text: {text}"
                    )

    def test_split_text_by_sentence_and_tokens_round_trip(self):
        """
        Full pipeline test: naive sentence split -> chunk by tokens -> re-join
        ensures the exact original text is recovered.
        """
        max_tokens = 30 
        for text in self.TEST_TEXTS:
            with self.subTest(text=text):
                chunks = split_text_by_sentence_and_tokens(text, self.tokenizer, max_tokens)
                rejoined = "".join(chunks)
                self.assertEqual(
                    rejoined, 
                    text, 
                    f"Pipeline did not preserve the original text for: {text}"
                )

    def test_split_text_by_sentence_and_tokens_token_limit(self):
        """
        Check that *each* sub-chunk from split_text_by_sentence_and_tokens
        respects the max_tokens limit.
        """
        max_tokens = 10
        for text in self.TEST_TEXTS:
            with self.subTest(text=text):
                chunks = split_text_by_sentence_and_tokens(text, self.tokenizer, max_tokens=max_tokens)
                for ch in chunks:
                    n_toks = len(self.tokenizer.encode(ch, add_special_tokens=False))
                    self.assertLessEqual(
                        n_toks, 
                        max_tokens, 
                        f"Chunk exceeds max_tokens limit for text: {text}"
                    )

    def test_edge_case(self):
        txt = 'Massage therapy may be helpful for neck and shoulder pain, but it seems to provide only short-term relief.\n- Cancer Pain. '
        chunks = split_text_by_sentence_and_tokens(txt, self.tokenizer, max_tokens=2000)
        print(chunks)
        self.assertEqual(len(chunks), 2)



if __name__ == '__main__':
    unittest.main()

