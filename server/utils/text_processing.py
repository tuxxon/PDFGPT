import re
import logging

logger = logging.getLogger(__name__)

def preprocess(text):
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text

def text_to_chunks(texts, file_ref, word_length=150, start_page=1):
    """
    텍스트를 지정된 단어 길이로 나누고, 파일별 참조 번호와 페이지 번호를 포함한 레퍼런스를 생성합니다.

    Args:
        texts (list): PDF에서 추출한 텍스트 리스트
        file_ref (str): 파일별 고유 참조 번호 (예: "Ref1")
        word_length (int): 하나의 텍스트 조각에 포함될 단어 수
        start_page (int): 텍스트 조각 생성 시 시작 페이지 번호

    Returns:
        list: 텍스트 조각 리스트, 각 조각은 파일 참조 번호와 페이지 번호를 포함
    """
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
            # 파일별 참조 번호와 페이지 번호를 포함한 레퍼런스 생성
            chunk = f'"{chunk}" Ref: {file_ref}, P: {idx+start_page}]'
            chunks.append(chunk)
    
    logger.info(f"Text split into {len(chunks)} chunks")
    return chunks
