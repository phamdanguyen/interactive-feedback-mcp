#!/usr/bin/env python3
"""
Interactive Feedback MCP Server - Web Deployment Version
Deployable to Railway, Render, Heroku, etc.
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import subprocess
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Create FastAPI app
app = FastAPI(
    title="Interactive Feedback MCP Server",
    description="Web-deployable version of Interactive Feedback MCP for AI development tools",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def first_line(text: str) -> str:
    """Get first line of text"""
    return text.split("\n")[0].strip()

def launch_feedback_ui(project_directory: str, summary: str) -> dict[str, str]:
    """Launch feedback UI and return result"""
    # Create a temporary file for the feedback result
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = tmp.name

    try:
        # Get the path to feedback_ui.py relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_ui_path = os.path.join(script_dir, "feedback_ui.py")

        # Run feedback_ui.py as a separate process
        args = [
            sys.executable,
            "-u",
            feedback_ui_path,
            "--project-directory", project_directory,
            "--prompt", summary,
            "--output-file", output_file
        ]
        
        result = subprocess.run(
            args,
            check=False,
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to launch feedback UI: {result.returncode}")

        # Read the result from the temporary file
        with open(output_file, 'r') as f:
            result = json.load(f)
        os.unlink(output_file)
        return result
        
    except Exception as e:
        if os.path.exists(output_file):
            os.unlink(output_file)
        raise e

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Interactive Feedback MCP Server",
        "version": "1.0.0",
        "status": "running",
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
        "service": "interactive-feedback-mcp",
        "version": "1.0.0",
        "timestamp": asyncio.get_event_loop().time()
    }

@app.post("/api/interactive-feedback")
async def api_interactive_feedback(request: dict):
    """Interactive feedback API endpoint"""
    try:
        project_directory = request.get("project_directory", "")
        summary = request.get("summary", "")
        
        if not project_directory or not summary:
            raise HTTPException(
                status_code=400,
                detail="project_directory and summary are required"
            )
        
        # Log the feedback request
        logger.info(f"Interactive feedback request from {project_directory}")
        logger.info(f"Summary: {summary}")
        
        # For web deployment, we'll simulate the feedback process
        # In a real deployment, you might want to implement a different feedback mechanism
        result = {
            "status": "success",
            "message": "Interactive feedback request received",
            "data": {
                "project_directory": first_line(project_directory),
                "summary": first_line(summary),
                "timestamp": asyncio.get_event_loop().time(),
                "server_url": f"http://{HOST}:{PORT}",
                "feedback": "User feedback received via web API"
            }
        }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error handling interactive feedback: {e}")
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
        }
    }

if __name__ == "__main__":
    logger.info(f"Starting Interactive Feedback MCP Server on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
