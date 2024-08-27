from dotenv import load_dotenv
import os
import re
import shutil
import urllib.request
from pathlib import Path
from tempfile import NamedTemporaryFile

import fitz
import numpy as np
import tensorflow_hub as hub
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.neighbors import NearestNeighbors
from litellm import completion

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용. 실제 운영 환경에서는 구체적인 오리진을 지정하는 것이 좋습니다.
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

# Load the Universal Sentence Encoder
EMBED = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")

recommender = None

def download_pdf(url, output_path):
    urllib.request.urlretrieve(url, output_path)

def preprocess(text):
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text

def pdf_to_text(path, start_page=1, end_page=None):
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
    return text_list

def text_to_chunks(texts, word_length=150, start_page=1):
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
    return chunks

class SemanticSearch:
    def __init__(self):
        self.use = EMBED
        self.fitted = False

    def fit(self, data, batch=1000, n_neighbors=5):
        self.data = data
        self.embeddings = self.get_text_embedding(data, batch=batch)
        n_neighbors = min(n_neighbors, len(self.embeddings))
        self.nn = NearestNeighbors(n_neighbors=n_neighbors)
        self.nn.fit(self.embeddings)
        self.fitted = True

    def __call__(self, text, return_data=True):
        inp_emb = self.use([text])
        neighbors = self.nn.kneighbors(inp_emb, return_distance=False)[0]

        if return_data:
            return [self.data[i] for i in neighbors]
        else:
            return neighbors

    def get_text_embedding(self, texts, batch=1000):
        embeddings = []
        for i in range(0, len(texts), batch):
            text_batch = texts[i : (i + batch)]
            emb_batch = self.use(text_batch)
            embeddings.append(emb_batch)
        embeddings = np.vstack(embeddings)
        return embeddings

def load_recommender(path, start_page=1):
    global recommender
    if recommender is None:
        recommender = SemanticSearch()

    texts = pdf_to_text(path, start_page=start_page)
    chunks = text_to_chunks(texts, start_page=start_page)
    recommender.fit(chunks)
    return 'Corpus Loaded.'

def generate_answer(question, openAI_key):
    topn_chunks = recommender(question)
    prompt = "search results:\n\n"
    for c in topn_chunks:
        prompt += c + '\n\n'

    prompt += (
        "Instructions: Compose a comprehensive reply to the query using the search results given. "
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
        messages=[{"content": prompt, "role": "user"}]
        completions = completion(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=512,
            n=1,
            stop=None,
            temperature=0.7,
            api_key=openAI_key
        )
        answer = completions['choices'][0]['message']['content']
    except Exception as e:
        answer = f'API Error: {str(e)}'
    
    return answer

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a PDF.")
    
    file_path = os.path.join('uploads', file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    load_recommender(file_path)
    
    return JSONResponse(content={"message": "PDF uploaded and processed successfully"}, status_code=200)

@app.post("/upload_pdf_url")
async def upload_pdf_url(url: str):
    file_path = os.path.join('uploads', 'downloaded_pdf.pdf')
    download_pdf(url, file_path)
    
    load_recommender(file_path)
    
    return JSONResponse(content={"message": "PDF downloaded from URL and processed successfully"}, status_code=200)

class Question(BaseModel):
    question: str

@app.post("/ask_question")
async def ask_question(question: Question):
    if recommender is None:
        raise HTTPException(status_code=400, detail="No PDF has been uploaded and processed yet")
    
    openAI_key = os.environ.get("OPENAI_API_KEY")
    if not openAI_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not found in environment variables")
    
    answer = generate_answer(question.question, openAI_key)
    
    return JSONResponse(content={"answer": answer}, status_code=200)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)