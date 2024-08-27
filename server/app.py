from dotenv import load_dotenv
import os
import re
import shutil
import urllib.request
from pathlib import Path
from tempfile import NamedTemporaryFile
from enum import Enum
import logging

import fitz
import numpy as np
import tensorflow_hub as hub
from openai import OpenAI
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.neighbors import NearestNeighbors

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Loading Universal Sentence Encoder...")
USE_MODEL = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
logger.info("Universal Sentence Encoder loaded successfully.")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
logger.info("OpenAI client initialized.")

class EmbeddingModel(str, Enum):
    USE = "use"
    ADA = "ada"

class Language(str, Enum):
    ENGLISH = "english"
    KOREAN = "korean"

recommender = None

def download_pdf(url, output_path):
    logger.info(f"Downloading PDF from URL: {url}")
    urllib.request.urlretrieve(url, output_path)
    logger.info(f"PDF downloaded and saved to: {output_path}")

def preprocess(text):
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text

def pdf_to_text(path, start_page=1, end_page=None):
    logger.info(f"Converting PDF to text: {path}")
    doc = fitz.open(path)
    total_pages = doc.page_count

    if end_page is None:
        end_page = total_pages

    text_list = []

    for i in range(start_page - 1, end_page):
        text = doc.load_page(i).get_text("text")
        text = preprocess(text)
        text_list.append(text)

    doc.close()
    logger.info(f"PDF converted to text successfully. Total pages processed: {end_page - start_page + 1}")
    return text_list

def text_to_chunks(texts, word_length=150, start_page=1):
    logger.info("Splitting text into chunks")
    text_toks = [t.split(' ') for t in texts]
    chunks = []

    for idx, words in enumerate(text_toks):
        for i in range(0, len(words), word_length):
            chunk = words[i : i + word_length]
            if (i + word_length) > len(words) and (len(chunk) < word_length) and (len(text_toks) != (idx + 1)):
                text_toks[idx + 1] = chunk + text_toks[idx + 1]
                continue
            chunk = ' '.join(chunk).strip()
            chunk = f'[Page no. {idx+start_page}] "{chunk}"'
            chunks.append(chunk)
    
    logger.info(f"Text split into {len(chunks)} chunks")
    return chunks

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
            return self.get_use_embedding(texts, batch)
        elif self.model == EmbeddingModel.ADA:
            return self.get_ada_embedding(texts, batch)

    def get_use_embedding(self, texts, batch=1000):
        logger.info("Getting USE embeddings")
        embeddings = []
        for i in range(0, len(texts), batch):
            text_batch = texts[i : (i + batch)]
            emb_batch = USE_MODEL(text_batch)
            embeddings.append(emb_batch)
        return np.vstack(embeddings)

    def get_ada_embedding(self, texts, batch=1000):
        logger.info("Getting ADA embeddings")
        embeddings = []
        for i in range(0, len(texts), batch):
            text_batch = texts[i : (i + batch)]
            response = client.embeddings.create(input=text_batch, model="text-embedding-ada-002")
            emb_batch = [item.embedding for item in response.data]
            embeddings.extend(emb_batch)
        return np.array(embeddings)

def load_recommender(path, start_page=1, model: EmbeddingModel = EmbeddingModel.USE):
    global recommender
    logger.info(f"Loading recommender with model: {model}")
    recommender = SemanticSearch(model)

    texts = pdf_to_text(path, start_page=start_page)
    chunks = text_to_chunks(texts, start_page=start_page)
    recommender.fit(chunks)
    logger.info("Recommender loaded successfully")
    return 'Corpus Loaded.'

def generate_answer(question, language, openAI_key):
    logger.info(f"Generating answer in {language}")
    topn_chunks = recommender(question)
    prompt = "search results:\n\n"
    for c in topn_chunks:
        prompt += c + '\n\n'

    language_instruction = "Answer in English" if language == Language.ENGLISH else "답변은 한국어로 작성해주세요"
    
    prompt += (
        f"Instructions: {language_instruction}. Compose a comprehensive reply to the query using the search results given. "
        "Cite each reference using [Page Number] notation (every result has this number at the beginning). "
        "Citation should be done at the end of each sentence. If the search results mention multiple subjects "
        "with the same name, create separate answers for each. Only include information found in the results and "
        "don't add any additional information. Make sure the answer is correct and don't output false content. "
        "If the text does not relate to the query, simply state 'Text Not Found in PDF'. Ignore outlier "
        "search results which has nothing to do with the question. Only answer what is asked. The "
        "answer should be short and concise. Answer step-by-step. \n\n"
        f"Query: {question}\nAnswer: "
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            n=1,
            stop=None,
            temperature=0.7
        )
        answer = response.choices[0].message.content
        logger.info("Answer generated successfully")
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        answer = f'API Error: {str(e)}'

    return answer

@app.post("/upload_pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    model: EmbeddingModel = Form(EmbeddingModel.USE)
):
    logger.info(f"Received PDF upload request. Filename: {file.filename}, Model: {model}")
    if not file.filename.endswith('.pdf'):
        logger.warning(f"Invalid file format: {file.filename}")
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a PDF.")

    file_path = os.path.join('uploads', file.filename)
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        logger.info(f"File saved successfully: {file_path}")
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    try:
        logger.info(f"Processing PDF with {model} model")
        load_recommender(file_path, model=model)
        logger.info("PDF processed successfully")
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

    return JSONResponse(content={
        "message": f"PDF uploaded and processed successfully using {model} model",
        "model_used": model
    }, status_code=200)

@app.post("/upload_pdf_url")
async def upload_pdf_url(url: str, model: EmbeddingModel = EmbeddingModel.USE):
    logger.info(f"Received PDF URL upload request. URL: {url}, Model: {model}")
    file_path = os.path.join('uploads', 'downloaded_pdf.pdf')
    try:
        download_pdf(url, file_path)
    except Exception as e:
        logger.error(f"Error downloading PDF: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error downloading PDF: {str(e)}")

    try:
        logger.info(f"Processing PDF with {model} model")
        load_recommender(file_path, model=model)
        logger.info("PDF processed successfully")
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

    return JSONResponse(content={
        "message": f"PDF downloaded from URL and processed successfully using {model} model",
        "model_used": model
    }, status_code=200)

class Question(BaseModel):
    question: str

@app.post("/ask_question")
async def ask_question(
    question: Question,
    language: Language = Query(default=Language.ENGLISH, description="Select the language for the answer")
):
    logger.info(f"Received question: {question.question}, Language: {language}")
    if recommender is None:
        logger.warning("No PDF has been uploaded and processed yet")
        raise HTTPException(status_code=400, detail="No PDF has been uploaded and processed yet")

    openAI_key = os.environ.get("OPENAI_API_KEY")
    if not openAI_key:
        logger.error("OpenAI API key not found in environment variables")
        raise HTTPException(status_code=400, detail="OpenAI API key not found in environment variables")

    answer = generate_answer(question.question, language, openAI_key)
    logger.info("Answer generated successfully")

    return JSONResponse(content={
        "answer": answer,
        "model_used": recommender.model,
        "language": language
    }, status_code=200)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    logger.info("Starting server...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)