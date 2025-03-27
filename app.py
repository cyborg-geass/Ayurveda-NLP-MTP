from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from multi_agent.agents_graph import agentic_rag, memory
import uvicorn

app = FastAPI(title="Ayurveda Companion API")

class QueryRequest(BaseModel):
    question: str
    history: List[Dict[str, str]] = []

class QueryResponse(BaseModel):
    answer: str
    history: List[Dict[str, str]]

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

@app.post("/askanythingayurveda", response_model=QueryResponse)
def ask_anything_ayurveda(query: QueryRequest):
    try:
        answer, updated_history = process_query(query.question, query.history)
        return QueryResponse(answer=answer, history=updated_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
