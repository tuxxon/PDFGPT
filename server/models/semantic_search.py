from sklearn.neighbors import NearestNeighbors
from models.embedding_model import get_use_embedding, get_ada_embedding, EmbeddingModel
import logging

logger = logging.getLogger(__name__)

class SemanticSearch:
    def __init__(self, model: EmbeddingModel = EmbeddingModel.USE):
        self.model = model
        self.fitted = False
        logger.info(f"SemanticSearch initialized with model: {model}")

    def fit(self, data, batch=1000, n_neighbors=5):
        logger.info("Fitting SemanticSearch model")
        self.data = data
        self.embeddings = self.get_text_embedding(data, batch=batch)
        n_neighbors = min(n_neighbors, len(self.embeddings))
        self.nn = NearestNeighbors(n_neighbors=n_neighbors)
        self.nn.fit(self.embeddings)
        self.fitted = True
        logger.info("SemanticSearch model fitted successfully")

    def __call__(self, text, return_data=True):
        logger.info("Performing semantic search")
        inp_emb = self.get_text_embedding([text])[0]
        neighbors = self.nn.kneighbors([inp_emb], return_distance=False)[0]

        if return_data:
            return [self.data[i] for i in neighbors]
        else:
            return neighbors

    def get_text_embedding(self, texts, batch=1000):
        logger.info(f"Getting text embeddings using {self.model} model")
        if self.model == EmbeddingModel.USE:
            return get_use_embedding(texts, batch)
        elif self.model == EmbeddingModel.ADA:
            return get_ada_embedding(texts, batch)
