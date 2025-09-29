#!/usr/bin/env python3
"""
Simple Interactive Feedback MCP Server for Railway deployment
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
import time

app = FastAPI(title="Interactive Feedback MCP Server")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "service": "Interactive Feedback MCP Server",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/api/interactive-feedback")
def interactive_feedback(request: dict):
    """Interactive feedback endpoint"""
    try:
        project_dir = request.get("project_directory", "")
        summary = request.get("summary", "")
        
        if not project_dir or not summary:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # For now, return a success response
        # In production, this would handle actual feedback collection
        return {
            "status": "success",
            "message": "Interactive feedback received",
            "data": {
                "project_directory": project_dir,
                "summary": summary,
                "feedback": "User feedback processed successfully",
                "timestamp": time.time()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
