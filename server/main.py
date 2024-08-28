from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api import *

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.post("/upload_pdf")(upload_pdf)
app.post("/upload_pdf_url")(upload_pdf_url)
app.post("/ask_question")(ask_question)
app.post("/embed_all_pdfs")(embed_all_pdfs)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
