#!/usr/bin/env python3
"""
Interactive Feedback MCP Server for Google Colab
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import time
import os

# Create FastAPI app
app = FastAPI(
    title="Interactive Feedback MCP Server - Colab",
    description="Interactive Feedback MCP Server running on Google Colab",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def first_line(text: str) -> str:
    """Get first line of text"""
    return text.split("\n")[0].strip()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Interactive Feedback MCP Server - Colab",
        "version": "1.0.0",
        "status": "running",
        "platform": "Google Colab",
        "endpoints": {
            "health": "/health",
            "interactive_feedback": "/api/interactive-feedback"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "interactive-feedback-mcp-colab",
        "version": "1.0.0",
        "timestamp": time.time(),
        "platform": "Google Colab"
    }

@app.post("/api/interactive-feedback")
async def api_interactive_feedback(request: dict):
    """Interactive feedback API endpoint for Colab"""
    try:
        project_directory = request.get("project_directory", "")
        summary = request.get("summary", "")
        
        if not project_directory or not summary:
            raise HTTPException(
                status_code=400,
                detail="project_directory and summary are required"
            )
        
        # Log the feedback request
        print(f"Interactive feedback request from {project_directory}")
        print(f"Summary: {summary}")
        
        # For Colab deployment, we'll return a structured response
        result = {
            "status": "success",
            "message": "Interactive feedback request received via Google Colab",
            "data": {
                "project_directory": first_line(project_directory),
                "summary": first_line(summary),
                "timestamp": time.time(),
                "platform": "Google Colab",
                "feedback": "User feedback processed successfully via Colab server"
            }
        }
        
        return result
        
    except Exception as e:
        print(f"Error handling interactive feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/interactive-feedback")
async def get_interactive_feedback_info():
    """Get interactive feedback API info"""
    return {
        "method": "POST",
        "endpoint": "/api/interactive-feedback",
        "parameters": {
            "project_directory": "string (required) - Full path to project directory",
            "summary": "string (required) - Short summary of changes"
        },
        "example": {
            "project_directory": "/path/to/project",
            "summary": "Implemented new feature"
        },
        "platform": "Google Colab"
    }

if __name__ == "__main__":
    # For Colab, we need to run on all interfaces and use ngrok or similar
    print("Starting Interactive Feedback MCP Server on Google Colab...")
    print("Use ngrok or Colab's built-in public URL feature to expose the server")
    
    # Run on all interfaces for Colab
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
