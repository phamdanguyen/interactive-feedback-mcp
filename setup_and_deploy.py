#!/usr/bin/env python3
"""
Setup and Deploy Interactive Feedback MCP Server
"""

import os
import sys
import subprocess
import json
import time
import requests

def run_command(command, description):
    """Run a command and return result"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return result.stdout.strip()
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return None

def test_server(url):
    """Test if server is running"""
    try:
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ Server is running at {url}")
            return True
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

def main():
    print("🚀 Interactive Feedback MCP Server Setup & Deployment")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("railway_server.py"):
        print("❌ Error: railway_server.py not found. Please run from the project directory.")
        return
    
    # Step 1: Install dependencies
    print("\n📦 Step 1: Installing dependencies...")
    run_command("pip install fastapi uvicorn", "Installing FastAPI and Uvicorn")
    
    # Step 2: Test server locally
    print("\n🧪 Step 2: Testing server locally...")
    print("Starting server in background...")
    
    # Start server in background
    server_process = subprocess.Popen([
        sys.executable, "railway_server.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    
    # Test local server
    if test_server("http://localhost:8000"):
        print("✅ Local server test passed")
    else:
        print("❌ Local server test failed")
    
    # Stop local server
    server_process.terminate()
    
    # Step 3: Check Git status
    print("\n📋 Step 3: Checking Git status...")
    git_status = run_command("git status --porcelain", "Checking Git status")
    if git_status:
        print("📝 Files to commit:")
        print(git_status)
        
        # Ask user if they want to commit
        response = input("\n❓ Do you want to commit and push changes? (y/n): ")
        if response.lower() == 'y':
            run_command("git add .", "Adding files to Git")
            run_command("git commit -m 'Setup Interactive Feedback MCP Server deployment'", "Committing changes")
            run_command("git push origin main", "Pushing to GitHub")
            print("✅ Changes pushed to GitHub")
        else:
            print("⏭️ Skipping Git operations")
    else:
        print("✅ No changes to commit")
    
    # Step 4: Deployment instructions
    print("\n🚀 Step 4: Deployment Instructions")
    print("=" * 40)
    
    print("\n📋 Railway Deployment:")
    print("1. Install Railway CLI: npm install -g @railway/cli")
    print("2. Login: railway login")
    print("3. Deploy: railway deploy")
    print("4. Get URL: railway status")
    
    print("\n📋 Render Deployment:")
    print("1. Go to https://render.com")
    print("2. Connect your GitHub repository")
    print("3. Create new Web Service")
    print("4. Configure:")
    print("   - Build Command: pip install fastapi uvicorn")
    print("   - Start Command: python railway_server.py")
    print("   - Environment: Python 3")
    
    print("\n📋 Heroku Deployment:")
    print("1. Install Heroku CLI")
    print("2. Login: heroku login")
    print("3. Create app: heroku create your-app-name")
    print("4. Deploy: git push heroku main")
    
    # Step 5: Cursor configuration
    print("\n🎯 Step 5: Cursor Configuration")
    print("=" * 40)
    
    cursor_config = {
        "mcpServers": {
            "interactive-feedback-mcp": {
                "command": "curl",
                "args": [
                    "-X", "POST",
                    "https://your-deployed-url.com/api/interactive-feedback",
                    "-H", "Content-Type: application/json",
                    "-d", "@-"
                ],
                "timeout": 600
            }
        }
    }
    
    print("Add this to your Cursor mcp.json:")
    print(json.dumps(cursor_config, indent=2))
    
    print("\n📋 Manual Testing:")
    print("After deployment, test with:")
    print("curl https://your-deployed-url.com/health")
    print("curl -X POST https://your-deployed-url.com/api/interactive-feedback \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"project_directory\": \"/test\", \"summary\": \"Test feedback\"}'")
    
    print("\n✅ Setup complete!")
    print("🔗 Next: Deploy to your chosen platform and update Cursor configuration")

if __name__ == "__main__":
    main()
