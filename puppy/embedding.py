# from langchain_community.embeddings import OpenAIEmbeddings
import os
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer


class LocalLongTextEmbedder:
    """
    Embedding function using sentence-transformers/all-MiniLM-L6-v2 as embedding backend.
    If the input is larger than the context size (token limit), the input is split into chunks
    and embedded separately. The final embedding is the average of the embeddings of the chunks.
    """

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 512,  # effective input limit of MiniLM-L6-v2 is ~256 tokens
        verbose: bool = False,
    ) -> None:
        self.model_name = embedding_model
        self.chunk_size = chunk_size
        self.verbose = verbose
        self.model = SentenceTransformer(self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

    def _tokenize_text(self, text: str) -> List[str]:
        """Splits long text into chunks based on token length."""
        tokens = self.tokenizer.tokenize(text)
        chunks = []
        for i in range(0, len(tokens), self.chunk_size):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_text = self.tokenizer.convert_tokens_to_string(chunk_tokens)
            chunks.append(chunk_text)
        return chunks

    def _embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        if isinstance(text, str):
            text = [text]

        embeddings = []
        for doc in text:
            chunks = self._tokenize_text(doc)
            if self.verbose:
                print(f"Embedding {len(chunks)} chunk(s) from input text.")

            chunk_embeddings = self.model.encode(chunks)
            avg_embedding = np.mean(chunk_embeddings, axis=0)
            embeddings.append(avg_embedding)

        return embeddings

    def __call__(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Encodes input text(s) and returns averaged embedding as np.ndarray.
        """
        return np.array(self._embed(text)).astype("float32")

    def get_embedding_dimension(self) -> int:
        """Returns embedding dimension for the selected model."""
        return self.model.get_sentence_embedding_dimension()


# embedder = LocalLongTextEmbedder(verbose = True)
# text = "This is a long article or passage that you want to embed. " * 100  # simulate long input
# embedding = embedder(text)
# print("Embedding shape:", embedding.shape)
