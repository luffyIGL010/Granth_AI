
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chat import chat_reply, reset_chat


from rag import (
    retrieve_context,
    generate_answer,
    collection as pdf_collection
)

from video_rag import (
    retrieve_video_context,
    generate_video_answer,
    collection as video_collection,
    format_timestamp,
    create_timestamp_url
)


# ==========================================
# FASTAPI CONFIGURATION
# ==========================================

app = FastAPI(
    title="Granth AI",
    description="PDF and YouTube RAG Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ==========================================
# REQUEST MODEL
# ==========================================

class QuestionRequest(BaseModel):
    question: str


class ChatRequest(BaseModel):
    session_id: str
    message: str

def validate_question(question):

    question = question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    return question


# ==========================================
# PDF RESULT
# ==========================================

def get_pdf_result(question):

    contexts = retrieve_context(question)

    answer = generate_answer(
        question,
        contexts
    )

    sources = []
    seen = set()

    for item in contexts:

        metadata = item["metadata"]

        key = (
            metadata["book_name"],
            metadata["page"]
        )

        if key in seen:
            continue

        seen.add(key)

        sources.append({
            "book_name": metadata["book_name"],
            "page": metadata["page"],
            "similarity": round(
                float(item["similarity"]), 3
            )
        })

    return {
        "answer": answer,
        "sources": sources
    }


# ==========================================
# YOUTUBE RESULT
# ==========================================

def get_video_result(question):

    contexts = retrieve_video_context(question)

    answer = generate_video_answer(
        question,
        contexts
    )

    sources = []
    seen = set()

    for item in contexts:

        metadata = item["metadata"]

        timestamp = format_timestamp(
            metadata["start"]
        )

        key = (
            metadata["video_id"],
            timestamp
        )

        if key in seen:
            continue

        seen.add(key)

        sources.append({
            "video_title": metadata["video_title"],
            "video_url": metadata["video_url"],
            "timestamp": timestamp,
            "start_seconds": metadata["start"],
            "watch_url": create_timestamp_url(
                metadata["video_url"],
                metadata["start"]
            ),
            "similarity": round(
                float(item["final_score"]), 3
            )
        })

    return {
        "answer": answer,
        "sources": sources
    }


# ==========================================
# HOME ROUTE
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Granth AI API is running!",
        "pdf_chunks": pdf_collection.count(),
        "video_chunks": video_collection.count()
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "pdf_chunks": pdf_collection.count(),
        "video_chunks": video_collection.count()
    }


# ==========================================
# PDF API
# ==========================================

@app.post("/ask")
def ask_pdf(request: QuestionRequest):

    question = validate_question(
        request.question
    )

    return {
        "question": question,
        "source_type": "pdf",
        **get_pdf_result(question)
    }


# ==========================================
# VIDEO API
# ==========================================

@app.post("/ask-video")
def ask_video(request: QuestionRequest):

    question = validate_question(
        request.question
    )

    return {
        "question": question,
        "source_type": "youtube",
        **get_video_result(question)
    }


# ==========================================
# COMBINED API
# ==========================================

@app.post("/ask-all")
def ask_all(request: QuestionRequest):

    question = validate_question(
        request.question
    )

    pdf_result = get_pdf_result(question)

    video_result = get_video_result(question)

    return {
        "question": question,
        "pdf": pdf_result,
        "youtube": video_result
    }



@app.post("/chat")
def chat(request: ChatRequest):

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Please enter a message."
        )

    try:
        reply, suggestions = chat_reply(
            request.session_id,
            message
        )
    except Exception as error:
        print(f"Chat error: {error}")
        raise HTTPException(
            status_code=500,
            detail="Chat model se jawab nahi aaya."
        )

    return {
        "session_id": request.session_id,
        "reply": reply,
        "suggestions": suggestions
    }