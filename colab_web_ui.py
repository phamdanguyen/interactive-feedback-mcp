# Colab Web UI for Interactive Feedback MCP
# Simple web-based replacement for feedback_ui.py
# Compatible with Google Colab environment

import os
import sys
import json
import argparse
import threading
import time
from typing import Optional, TypedDict
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

class FeedbackResult(TypedDict):
    command_logs: str
    interactive_feedback: str

class FeedbackConfig(TypedDict):
    run_command: str
    execute_automatically: bool

# Global variables for feedback
feedback_result: Optional[FeedbackResult] = None
feedback_config: FeedbackConfig = {
    "run_command": "",
    "execute_automatically": False
}
current_project_directory = ""
current_prompt = ""
command_logs = []

# Create FastAPI app
app = FastAPI(
    title="Interactive Feedback MCP - Colab Web UI",
    description="Web-based feedback UI for Google Colab",
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

@app.get("/", response_class=HTMLResponse)
async def feedback_form():
    """Main feedback form"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Interactive Feedback MCP - Colab</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #1e1e1e;
                color: #ffffff;
            }}
            .container {{
                background-color: #2d2d2d;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .prompt {{
                background-color: #3d3d3d;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
                border-left: 4px solid #42a5f5;
            }}
            .command-section {{
                background-color: #3d3d3d;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .feedback-section {{
                background-color: #3d3d3d;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            input[type="text"], textarea {{
                width: 100%;
                padding: 10px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #404040;
                color: #ffffff;
                box-sizing: border-box;
            }}
            textarea {{
                min-height: 120px;
                resize: vertical;
            }}
            button {{
                background-color: #42a5f5;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin-right: 10px;
                margin-bottom: 10px;
            }}
            button:hover {{
                background-color: #1976d2;
            }}
            .log-output {{
                background-color: #1a1a1a;
                color: #00ff00;
                padding: 10px;
                border-radius: 4px;
                font-family: monospace;
                min-height: 200px;
                white-space: pre-wrap;
                overflow-y: auto;
                max-height: 400px;
            }}
            .hidden {{
                display: none;
            }}
            .status {{
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 10px;
            }}
            .success {{
                background-color: #2e7d32;
                color: white;
            }}
            .info {{
                background-color: #1976d2;
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Interactive Feedback MCP - Colab</h1>
            
            <div class="prompt">
                <h3>📝 Prompt:</h3>
                <p>{current_prompt}</p>
            </div>
            
            <div class="command-section">
                <h3>⚙️ Command Section</h3>
                <p><strong>Working Directory:</strong> {current_project_directory}</p>
                
                <form id="commandForm">
                    <label for="command">Command to run:</label>
                    <input type="text" id="command" name="command" placeholder="Enter command here..." value="{feedback_config['run_command']}">
                    <br><br>
                    
                    <button type="button" onclick="runCommand()">▶️ Run Command</button>
                    <button type="button" onclick="toggleLogs()">📋 Toggle Logs</button>
                    <button type="button" onclick="clearLogs()">🗑️ Clear Logs</button>
                    <br><br>
                    
                    <label>
                        <input type="checkbox" id="autoExecute" {'checked' if feedback_config['execute_automatically'] else ''}> 
                        Execute automatically on next run
                    </label>
                </form>
                
                <div id="logSection" class="hidden">
                    <h4>📋 Command Output:</h4>
                    <div id="logOutput" class="log-output"></div>
                </div>
            </div>
            
            <div class="feedback-section">
                <h3>💬 Feedback Section</h3>
                <form id="feedbackForm">
                    <label for="feedback">Your feedback:</label>
                    <textarea id="feedback" name="feedback" placeholder="Enter your feedback here..."></textarea>
                    <br><br>
                    
                    <button type="button" onclick="submitFeedback()">📤 Send Feedback</button>
                    <button type="button" onclick="submitEmpty()">⏭️ Skip (Empty Feedback)</button>
                </form>
            </div>
            
            <div id="status"></div>
        </div>
        
        <script>
            let logsVisible = false;
            let commandRunning = false;
            
            function showStatus(message, type = 'info') {{
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = `<div class="status ${{type}}">${{message}}</div>`;
            }}
            
            function toggleLogs() {{
                const logSection = document.getElementById('logSection');
                logsVisible = !logsVisible;
                logSection.classList.toggle('hidden');
            }}
            
            function clearLogs() {{
                document.getElementById('logOutput').textContent = '';
                showStatus('Logs cleared', 'info');
            }}
            
            async function runCommand() {{
                if (commandRunning) {{
                    showStatus('Command is already running...', 'info');
                    return;
                }}
                
                const command = document.getElementById('command').value;
                if (!command) {{
                    showStatus('Please enter a command', 'info');
                    return;
                }}
                
                commandRunning = true;
                showStatus('Running command...', 'info');
                
                try {{
                    const response = await fetch('/run-command', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }},
                        body: `command=${{encodeURIComponent(command)}}`
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        showStatus('Command executed successfully', 'success');
                        document.getElementById('logOutput').textContent = result.output;
                        if (!logsVisible) toggleLogs();
                    }} else {{
                        showStatus('Command failed: ' + result.error, 'info');
                        document.getElementById('logOutput').textContent = result.error;
                        if (!logsVisible) toggleLogs();
                    }}
                }} catch (error) {{
                    showStatus('Error running command: ' + error.message, 'info');
                }} finally {{
                    commandRunning = false;
                }}
            }}
            
            async function submitFeedback() {{
                const feedback = document.getElementById('feedback').value;
                
                try {{
                    const response = await fetch('/submit-feedback', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }},
                        body: `feedback=${{encodeURIComponent(feedback)}}`
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        showStatus('Feedback submitted successfully! Closing window...', 'success');
                        setTimeout(() => {{
                            window.close();
                        }}, 2000);
                    }} else {{
                        showStatus('Error submitting feedback: ' + result.error, 'info');
                    }}
                }} catch (error) {{
                    showStatus('Error submitting feedback: ' + error.message, 'info');
                }}
            }}
            
            async function submitEmpty() {{
                try {{
                    const response = await fetch('/submit-feedback', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }},
                        body: 'feedback='
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        showStatus('Empty feedback submitted. Closing window...', 'success');
                        setTimeout(() => {{
                            window.close();
                        }}, 2000);
                    }} else {{
                        showStatus('Error submitting feedback: ' + result.error, 'info');
                    }}
                }} catch (error) {{
                    showStatus('Error submitting feedback: ' + error.message, 'info');
                }}
            }}
            
            // Auto-execute if configured
            {f"runCommand();" if feedback_config['execute_automatically'] and feedback_config['run_command'] else ""}
        </script>
    </body>
    </html>
    """

@app.post("/run-command")
async def run_command(request: Request):
    """Run a command and return output"""
    try:
        form = await request.form()
        command = form.get("command", "")
        
        if not command:
            return {"success": False, "error": "No command provided"}
        
        # Update config
        feedback_config["run_command"] = command
        
        # Simulate command execution (in real implementation, you'd use subprocess)
        # For Colab, we'll just return a mock output
        output = f"$ {command}\n"
        output += f"Command executed in: {current_project_directory}\n"
        output += "Note: This is a mock execution in Colab environment.\n"
        output += "In real deployment, actual command execution would happen here.\n"
        
        # Store logs
        command_logs.append(output)
        
        return {
            "success": True,
            "output": output
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/submit-feedback")
async def submit_feedback(request: Request):
    """Submit feedback"""
    try:
        form = await request.form()
        feedback = form.get("feedback", "")
        
        # Store the result
        global feedback_result
        feedback_result = FeedbackResult(
            logs="".join(command_logs),
            interactive_feedback=feedback
        )
        
        return {
            "success": True,
            "message": "Feedback submitted successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/get-result")
async def get_result():
    """Get the feedback result (for external polling)"""
    return {
        "result": feedback_result,
        "ready": feedback_result is not None
    }

def feedback_ui(project_directory: str, prompt: str, output_file: Optional[str] = None) -> Optional[FeedbackResult]:
    """Main function to run the feedback UI"""
    global current_project_directory, current_prompt, feedback_result, command_logs
    
    # Reset state
    current_project_directory = project_directory
    current_prompt = prompt
    feedback_result = None
    command_logs = []
    
    # Start the web server
    def run_server():
        uvicorn.run(app, host="0.0.0.0", port=8080, log_level="error")
    
    # Start server in background
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    print(f"🌐 Feedback UI started at: http://localhost:8080")
    print(f"📁 Project: {project_directory}")
    print(f"💬 Prompt: {prompt}")
    print(f"⏳ Waiting for feedback...")
    
    # Poll for result
    while feedback_result is None:
        time.sleep(1)
    
    # Save result if output file specified
    if output_file and feedback_result:
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(feedback_result, f)
        return None
    
    return feedback_result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Colab feedback UI")
    parser.add_argument("--project-directory", default=os.getcwd(), help="The project directory to run the command in")
    parser.add_argument("--prompt", default="I implemented the changes you requested.", help="The prompt to show to the user")
    parser.add_argument("--output-file", help="Path to save the feedback result as JSON")
    args = parser.parse_args()
    
    result = feedback_ui(args.project_directory, args.prompt, args.output_file)
    if result:
        print(f"\nLogs collected: \n{result['logs']}")
        print(f"\nFeedback received:\n{result['interactive_feedback']}")
    sys.exit(0)
