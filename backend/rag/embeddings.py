# Local SentenceTransformer Embeddings placeholder
class LocalEmbedder:
    def embed_texts(self, texts: list):
        return [[0.0] * 384 for _ in texts]
