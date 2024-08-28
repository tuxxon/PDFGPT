import os
import logging
from fastapi import UploadFile, HTTPException, File
from fastapi.responses import JSONResponse
from urllib.parse import urlparse
from config.state import uploaded_files  # 전역 상태
from utils.pdf_processing import download_pdf

logger = logging.getLogger(__name__)

def get_unique_filename(directory, filename):
    """
    디렉토리 내에서 고유한 파일명을 생성합니다.
    """
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1

    return new_filename

async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a PDF.")

    file_path = os.path.join('uploads', file.filename)
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        uploaded_files.append(file_path)  # 파일 경로 저장
        logger.info(f"File uploaded successfully: {file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    return JSONResponse(content={"message": f"PDF '{file.filename}' uploaded successfully", "file_path": file_path}, status_code=200)



async def upload_pdf_url(url: str):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)

    if not filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="URL does not point to a PDF file.")

    # 고유한 파일명을 생성
    file_path = os.path.join('uploads', get_unique_filename('uploads', filename))

    try:
        download_pdf(url, file_path)
        uploaded_files.append(file_path)  # 파일 경로 저장
        logger.info(f"PDF downloaded and saved successfully: {file_path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error downloading PDF: {str(e)}")

    return JSONResponse(content={"message": "PDF downloaded successfully", "file_path": file_path}, status_code=200)
