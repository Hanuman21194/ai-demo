import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from test_function_calling_streaming import tool_calling
import uvicorn
from typing import List, Dict

app=FastAPI(title="GenAI Streaming App",
            description="execute streaming app",
            version="1.0.0")
class QueryRequest(BaseModel):
    messages: List[Dict[str, str]]
    model :str |None =None

@app.post("/ask")
async def ask_ai_endpoint  (request: QueryRequest):
    model_to_use = request.model 
    try:
        def event_generator():
            #full_response =""
            for chunk in tool_calling(messages=request.messages,model=model_to_use):
                if chunk:
                    yield chunk
                
        return StreamingResponse(event_generator(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    

           



