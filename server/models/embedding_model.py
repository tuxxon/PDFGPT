from enum import Enum
import numpy as np
import tensorflow_hub as hub
from openai import OpenAI
import logging
import os

logger = logging.getLogger(__name__)

class EmbeddingModel(str, Enum):
    USE = "use"
    ADA = "ada"

class Language(str, Enum):
    ENGLISH = "english"
    KOREAN = "korean"

logger.info("Loading Universal Sentence Encoder...")
USE_MODEL = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
logger.info("Universal Sentence Encoder loaded successfully.")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
logger.info("OpenAI client initialized.")

def get_use_embedding(texts, batch=1000):
    logger.info("Getting USE embeddings")
    embeddings = []
    for i in range(0, len(texts), batch):
        text_batch = texts[i : (i + batch)]
        emb_batch = USE_MODEL(text_batch)
        embeddings.append(emb_batch)
    return np.vstack(embeddings)

def get_ada_embedding(texts, batch=1000):
    logger.info("Getting ADA embeddings")
    embeddings = []
    for i in range(0, len(texts), batch):
        text_batch = texts[i : (i + batch)]
        response = client.embeddings.create(input=text_batch, model="text-embedding-ada-002")
        emb_batch = [item.embedding for item in response.data]
        embeddings.extend(emb_batch)
    return np.array(embeddings)
