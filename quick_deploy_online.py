#!/usr/bin/env python3
"""
Quick Deploy Interactive Feedback MCP Server Online
"""

import webbrowser
import os
import json

def open_railway():
    """Open Railway deployment page"""
    print("Opening Railway for deployment...")
    webbrowser.open("https://railway.app")
    print("\nRailway Deployment Steps:")
    print("1. Sign up/Login with GitHub")
    print("2. Click 'Deploy from GitHub repo'")
    print("3. Select: phamdanguyen/interactive-feedback-mcp")
    print("4. Railway will auto-detect Python and deploy")
    print("5. Copy the deployment URL")

def open_render():
    """Open Render deployment page"""
    print("Opening Render for deployment...")
    webbrowser.open("https://render.com")
    print("\nRender Deployment Steps:")
    print("1. Sign up/Login with GitHub")
    print("2. Click 'New +' → 'Web Service'")
    print("3. Connect: phamdanguyen/interactive-feedback-mcp")
    print("4. Configure:")
    print("   - Build Command: pip install fastapi uvicorn")
    print("   - Start Command: python railway_server.py")
    print("5. Deploy and copy URL")

def create_mcp_config_template():
    """Create MCP config template"""
    config = {
        "mcpServers": {
            "interactive-feedback-mcp": {
                "command": "curl",
                "args": [
                    "-X", "POST",
                    "https://YOUR-DEPLOYED-URL.com/api/interactive-feedback",
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
    
    with open("mcp_template.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("\n[SUCCESS] MCP template created: mcp_template.json")
    print("After deployment, update YOUR-DEPLOYED-URL.com with your actual URL")

def main():
    print("Quick Deploy Interactive Feedback MCP Server Online")
    print("=" * 60)
    
    print("\nGitHub Repository: phamdanguyen/interactive-feedback-mcp")
    print("Status: Ready for deployment")
    
    print("\nDeployment Options:")
    print("1. Railway (Recommended - Easiest)")
    print("2. Render (Alternative)")
    print("3. Show both options")
    
    choice = input("\nChoose option (1-3): ").strip()
    
    if choice == "1":
        open_railway()
        create_mcp_config_template()
    
    elif choice == "2":
        open_render()
        create_mcp_config_template()
    
    elif choice == "3":
        print("\nOpening both platforms...")
        open_railway()
        print("\n" + "="*40)
        open_render()
        create_mcp_config_template()
    
    else:
        print("Invalid choice. Showing both options...")
        open_railway()
        print("\n" + "="*40)
        open_render()
        create_mcp_config_template()
    
    print("\n" + "="*60)
    print("Next Steps After Deployment:")
    print("1. Wait for deployment to complete")
    print("2. Test your URL: https://your-url.com/health")
    print("3. Update mcp_template.json with your URL")
    print("4. Copy config to Cursor settings")
    print("5. Restart Cursor")
    print("6. Test with IT Manager Agent")
    
    print("\n[SUCCESS] Ready for online deployment!")

if __name__ == "__main__":
    main()
