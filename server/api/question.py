from fastapi import Query, HTTPException
from fastapi.responses import JSONResponse
import logging
from pydantic import BaseModel
from models.semantic_search import SemanticSearch
from models.embedding_model import Language, EmbeddingModel
from config.state import recommenders  # 전역 상태 임포트
from config.settings import client  # OpenAI client 임포트

logger = logging.getLogger(__name__)

class Question(BaseModel):
    question: str

async def ask_question(
    question: Question,
    language: Language = Query(default=Language.ENGLISH),
    model: EmbeddingModel = Query(default=EmbeddingModel.USE)  # 사용된 임베딩 모델을 받도록 수정
):
    if not recommenders:
        raise HTTPException(status_code=400, detail="No PDF has been uploaded and processed yet")

    # 선택된 모델을 기반으로 SemanticSearch 인스턴스를 생성
    recommender = SemanticSearch(model=model)
    recommender.fit(recommenders)

    answer = generate_answer(question.question, language, client, recommender)
    
    return JSONResponse(content={
        "answer": answer,
        "model_used": recommender.model,
        "language": language
    }, status_code=200)

def generate_answer(question, language, openAI, recommender_instance):
    logger.info(f"Generating answer in {language} using model {recommender_instance.model}")
    topn_chunks = recommender_instance(question)
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
        response = openAI.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            #max_tokens=512,
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
