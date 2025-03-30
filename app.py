import sys
from pathlib import Path
import os
import warnings
from dotenv import load_dotenv

load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from multi_agent.agents_graph import agentic_rag, memory
import uvicorn
import uuid
import redis
import json

app = FastAPI(title="Ayurveda Companion API")

app.mount("/static", StaticFiles(directory="static"), name="static")

chat_sessions: Dict[str, List[Dict[str, str]]] = {}
# REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True, ssl=True)
redis_client = redis.Redis(
    host='redis-18744.crce179.ap-south-1-1.ec2.redns.redis-cloud.com',
    port=18744,
    decode_responses=True,
    username="default",
    password="bor1qAwik9vEK8dXkhYJ6Ixq2Ggjt0yi",
    # ssl=True,
)
class QueryRequest(BaseModel):
    question: str
    history: List[Dict[str, str]] = []
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    history: List[Dict[str, str]]
    session_id: str

def get_history_from_redis(session_id: str) -> List[Dict[str, str]]:
    data = redis_client.get(f"session:{session_id}")
    if data:
        return json.loads(data)
    return []

def save_history_to_redis(session_id: str, history: List[Dict[str, str]]):
    redis_client.set(f"session:{session_id}", json.dumps(history))

def process_query(question: str, history: List[Dict[str, str]]):
    state = {
        "question": question,
        "generation": "",
        "web_search_needed": "no",
        "documents": [],
        "emotion": "neutral",
        "history": history
    }
    result = agentic_rag.invoke(state)
    return result['generation'], result['history']

@app.get("/")
def home():
    return {"message": "Welcome to the Ayurveda Companion API. Please visit /docs for API documentation."}

@app.post("/askanythingayurveda", response_model=QueryResponse)
def ask_anything_ayurveda(query: QueryRequest):
    session_id = query.session_id or str(uuid.uuid4())
    history = chat_sessions.get(session_id, [])
    # history = get_history_from_redis(session_id)
    try:
        answer, updated_history = process_query(query.question, history)
        chat_sessions[session_id] = updated_history
        # save_history_to_redis(session_id, updated_history)
        return QueryResponse(answer=answer, history=updated_history, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/askanythingayurveda")
def ask_question_get(question: str):
    # For GET testing purposes only; this won't include chat history
    try:
        answer, _ = process_query(question, [])
        return {"question": question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
