# Colab Server for Interactive Feedback MCP
# Modified server.py to work with web UI instead of desktop UI

import os
import sys
import json
import tempfile
import subprocess

from typing import Annotated, Dict

from fastmcp import FastMCP
from pydantic import Field

# Import the Colab web UI
from colab_web_ui import feedback_ui

# The log_level is necessary for Cline to work: https://github.com/jlowin/fastmcp/issues/81
mcp = FastMCP("Interactive Feedback MCP - Colab", log_level="ERROR")

def launch_feedback_ui(project_directory: str, summary: str) -> dict[str, str]:
    """Launch the Colab web-based feedback UI"""
    try:
        # Use the Colab web UI instead of desktop UI
        result = feedback_ui(project_directory, summary)
        
        if result is None:
            # If result is None, it means output was saved to file
            # This shouldn't happen in our case, but handle it gracefully
            return {
                "command_logs": "",
                "interactive_feedback": "No feedback received"
            }
        
        return result
        
    except Exception as e:
        # Fallback to simple response
        return {
            "command_logs": f"Error launching feedback UI: {str(e)}",
            "interactive_feedback": "Error occurred while getting feedback"
        }

def first_line(text: str) -> str:
    return text.split("\n")[0].strip()

@mcp.tool()
def interactive_feedback(
    project_directory: Annotated[str, Field(description="Full path to the project directory")],
    summary: Annotated[str, Field(description="Short, one-line summary of the changes")],
) -> Dict[str, str]:
    """Request interactive feedback for a given project directory and summary"""
    return launch_feedback_ui(first_line(project_directory), first_line(summary))

if __name__ == "__main__":
    mcp.run(transport="stdio")