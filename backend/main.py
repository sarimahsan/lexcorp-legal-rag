import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from retriever import retrieve
from chat import ask
from ingest import ingest as run_ingest

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = FastAPI(title="LexCorp Legal RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ────────────────────────────
class ChatRequest(BaseModel):
    message: str
    history: list = []


class ChatResponse(BaseModel):
    answer: str
    sources: list = []


# ── Endpoints ─────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    try:
        rag = retrieve(req.message)

        if not rag["found"]:
            return ChatResponse(
                answer=rag["message"],
                sources=[]
            )

        answer = ask(
            query=req.message,
            chunks=rag["chunks"],
            history=req.history,
        )

        sources = [
            {"citation": c["citation"], "text": c["text"][:200], "score": c["score"]}
            for c in rag["chunks"]
        ]

        return ChatResponse(answer=answer, sources=sources)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ingest")
def ingest_endpoint():
    try:
        run_ingest()
        return {"status": "ok", "message": "Ingestion complete"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
