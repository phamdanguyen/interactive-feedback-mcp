#!/usr/bin/env python3
"""
Deploy Interactive Feedback MCP Server to Online Platform
"""

import subprocess
import json
import os
import time

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

def check_railway_cli():
    """Check if Railway CLI is installed"""
    print("Checking Railway CLI...")
    result = run_command("railway --version", "Checking Railway CLI")
    return result is not None

def install_railway_cli():
    """Install Railway CLI"""
    print("Installing Railway CLI...")
    
    # Check if npm is available
    npm_check = run_command("npm --version", "Checking npm")
    if not npm_check:
        print("[ERROR] npm not found. Please install Node.js first.")
        print("Download from: https://nodejs.org/")
        return False
    
    # Install Railway CLI
    result = run_command("npm install -g @railway/cli", "Installing Railway CLI")
    return result is not None

def deploy_to_railway():
    """Deploy to Railway"""
    print("\nDeploying to Railway...")
    
    # Check if Railway CLI is installed
    if not check_railway_cli():
        print("Railway CLI not found. Installing...")
        if not install_railway_cli():
            print("[ERROR] Failed to install Railway CLI")
            return False
    
    # Login to Railway
    print("\nPlease login to Railway...")
    print("This will open a browser window for authentication.")
    login_result = run_command("railway login", "Logging into Railway")
    
    if not login_result:
        print("[ERROR] Railway login failed")
        return False
    
    # Initialize Railway project
    print("\nInitializing Railway project...")
    init_result = run_command("railway init", "Initializing Railway project")
    
    if not init_result:
        print("[ERROR] Railway initialization failed")
        return False
    
    # Deploy to Railway
    print("\nDeploying to Railway...")
    deploy_result = run_command("railway up", "Deploying to Railway")
    
    if deploy_result:
        print("[SUCCESS] Deployment to Railway completed!")
        
        # Get deployment URL
        print("\nGetting deployment URL...")
        status_result = run_command("railway status", "Getting Railway status")
        
        if status_result:
            print("[SUCCESS] Deployment successful!")
            print(f"Status: {status_result}")
            
            # Create updated MCP config
            create_online_mcp_config()
            
            return True
        else:
            print("[WARNING] Could not get deployment status")
            return True  # Still consider successful if deploy worked
    else:
        print("[ERROR] Railway deployment failed")
        return False

def create_online_mcp_config():
    """Create MCP config for online deployment"""
    print("\nCreating online MCP configuration...")
    
    # For now, create a template that user can update with actual URL
    config = {
        "mcpServers": {
            "interactive-feedback-mcp-online": {
                "command": "curl",
                "args": [
                    "-X", "POST",
                    "https://YOUR-RAILWAY-URL.up.railway.app/api/interactive-feedback",
                    "-H", "Content-Type: application/json",
                    "-d", "@-"
                ],
                "timeout": 600,
                "autoApprove": [
                    "interactive_feedback"
                ]
            }
        }
    }
    
    with open("mcp_online.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("[SUCCESS] Online MCP configuration created: mcp_online.json")
    print("\nNext steps:")
    print("1. Check Railway dashboard for your deployment URL")
    print("2. Update mcp_online.json with your actual URL")
    print("3. Copy configuration to Cursor settings")
    print("4. Restart Cursor")

def deploy_to_render():
    """Deploy to Render (alternative)"""
    print("\nDeploy to Render (Alternative):")
    print("1. Go to https://render.com")
    print("2. Sign up/Login with GitHub")
    print("3. Click 'New +' → 'Web Service'")
    print("4. Connect GitHub repo: phamdanguyen/interactive-feedback-mcp")
    print("5. Configure:")
    print("   - Build Command: pip install fastapi uvicorn")
    print("   - Start Command: python railway_server.py")
    print("   - Environment: Python 3")
    print("6. Deploy")

def main():
    print("Deploy Interactive Feedback MCP Server Online")
    print("=" * 60)
    
    print("\nDeployment Options:")
    print("1. Railway (Automated)")
    print("2. Render (Manual)")
    print("3. Heroku (Manual)")
    
    choice = input("\nChoose deployment option (1-3): ").strip()
    
    if choice == "1":
        success = deploy_to_railway()
        if success:
            print("\n[SUCCESS] Railway deployment completed!")
            print("Check Railway dashboard for your URL and update mcp_online.json")
        else:
            print("\n[FAIL] Railway deployment failed")
            print("Try Render deployment instead")
            deploy_to_render()
    
    elif choice == "2":
        deploy_to_render()
    
    elif choice == "3":
        print("\nHeroku Deployment:")
        print("1. Install Heroku CLI")
        print("2. heroku login")
        print("3. heroku create your-app-name")
        print("4. git push heroku main")
    
    else:
        print("Invalid choice. Please run again and choose 1-3.")

if __name__ == "__main__":
    main()
