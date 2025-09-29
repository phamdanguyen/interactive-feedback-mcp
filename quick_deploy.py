#!/usr/bin/env python3
"""
Quick Deploy Interactive Feedback MCP Server
"""

import subprocess
import os
import sys

def run_command(command, description):
    """Run a command and return result"""
    print(f"[INFO] {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[SUCCESS] {description} completed")
            return result.stdout.strip()
        else:
            print(f"[ERROR] {description} failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"[ERROR] {description} error: {e}")
        return None

def main():
    print("Quick Deploy Interactive Feedback MCP Server")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("railway_server.py"):
        print("[ERROR] railway_server.py not found. Please run from the project directory.")
        return
    
    # Step 1: Install dependencies
    print("\n[STEP 1] Installing dependencies...")
    run_command("pip install fastapi uvicorn", "Installing FastAPI and Uvicorn")
    
    # Step 2: Test server import
    print("\n[STEP 2] Testing server import...")
    test_result = run_command("python -c \"from railway_server import app; print('Server imports successfully')\"", "Testing server import")
    
    if not test_result:
        print("[ERROR] Server import failed. Please check the code.")
        return
    
    # Step 3: Check Git status
    print("\n[STEP 3] Checking Git status...")
    git_status = run_command("git status --porcelain", "Checking Git status")
    if git_status:
        print("Files to commit:")
        print(git_status)
        
        # Ask user if they want to commit
        response = input("\nDo you want to commit and push changes? (y/n): ")
        if response.lower() == 'y':
            run_command("git add .", "Adding files to Git")
            run_command("git commit -m 'Fix Interactive Feedback MCP Server deployment'", "Committing changes")
            run_command("git push origin main", "Pushing to GitHub")
            print("[SUCCESS] Changes pushed to GitHub")
        else:
            print("[SKIP] Skipping Git operations")
    else:
        print("[INFO] No changes to commit")
    
    # Step 4: Deployment options
    print("\n[STEP 4] Deployment Options")
    print("=" * 40)
    
    print("\n1. Railway (Recommended - Free tier available):")
    print("   - Go to: https://railway.app")
    print("   - Connect GitHub: phamdanguyen/interactive-feedback-mcp")
    print("   - Deploy automatically")
    
    print("\n2. Render (Free tier available):")
    print("   - Go to: https://render.com")
    print("   - Connect GitHub: phamdanguyen/interactive-feedback-mcp")
    print("   - Create Web Service")
    print("   - Build Command: pip install fastapi uvicorn")
    print("   - Start Command: python railway_server.py")
    
    print("\n3. Heroku (Free tier discontinued, but still works):")
    print("   - Install Heroku CLI")
    print("   - heroku create your-app-name")
    print("   - git push heroku main")
    
    print("\n4. Local testing:")
    print("   - python railway_server.py")
    print("   - Test: curl http://localhost:8000/health")
    
    # Step 5: Cursor configuration
    print("\n[STEP 5] Cursor Configuration")
    print("=" * 40)
    
    print("After deployment, add this to your Cursor mcp.json:")
    print('{')
    print('  "mcpServers": {')
    print('    "interactive-feedback-mcp": {')
    print('      "command": "curl",')
    print('      "args": [')
    print('        "-X", "POST",')
    print('        "https://your-deployed-url.com/api/interactive-feedback",')
    print('        "-H", "Content-Type: application/json",')
    print('        "-d", "@-"')
    print('      ],')
    print('      "timeout": 600')
    print('    }')
    print('  }')
    print('}')
    
    print("\n[SUCCESS] Setup complete!")
    print("Next: Choose a deployment platform and update Cursor configuration")

if __name__ == "__main__":
    main()
