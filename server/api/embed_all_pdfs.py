from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
import logging
from config.state import uploaded_files, recommenders  # 전역 상태
from utils.text_processing import text_to_chunks
from models.semantic_search import SemanticSearch
from utils.pdf_processing import pdf_to_text

logger = logging.getLogger(__name__)

async def embed_all_pdfs(model: str = Query("use")):
    if not uploaded_files:
        raise HTTPException(status_code=400, detail="No PDF files have been uploaded yet.")

    try:
        for index, file_path in enumerate(uploaded_files):
            file_ref = f"Ref{index + 1}"  # 파일별 고유 참조 번호 생성
            texts = pdf_to_text(file_path)
            chunks = text_to_chunks(texts, file_ref)
            recommenders.extend(chunks)
        
        # 모델 학습
        recommender = SemanticSearch(model=model)
        recommender.fit(recommenders)
        
        logger.info("All PDFs processed successfully and integrated into the model")
        return JSONResponse(content={"message": "All PDFs processed successfully", "model_used": model}, status_code=200)
    except Exception as e:
        logger.error(f"Error processing PDFs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDFs: {str(e)}")
