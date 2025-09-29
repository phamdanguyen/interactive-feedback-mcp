#!/usr/bin/env python3
"""
Deploy Interactive Feedback MCP Server to Railway
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
    print("Deploying Interactive Feedback MCP Server to Railway")
    print("=" * 60)
    
    # Check if Railway CLI is installed
    print("\n[STEP 1] Checking Railway CLI...")
    railway_check = run_command("railway --version", "Checking Railway CLI")
    
    if not railway_check:
        print("\n[INFO] Railway CLI not found. Installing...")
        npm_check = run_command("npm --version", "Checking npm")
        if npm_check:
            run_command("npm install -g @railway/cli", "Installing Railway CLI")
        else:
            print("[ERROR] npm not found. Please install Node.js first.")
            print("Download from: https://nodejs.org/")
            return
    
    # Login to Railway
    print("\n[STEP 2] Railway Authentication...")
    print("Please login to Railway in your browser...")
    run_command("railway login", "Logging into Railway")
    
    # Initialize Railway project
    print("\n[STEP 3] Initializing Railway Project...")
    run_command("railway init", "Initializing Railway project")
    
    # Deploy to Railway
    print("\n[STEP 4] Deploying to Railway...")
    deploy_result = run_command("railway up", "Deploying to Railway")
    
    if deploy_result:
        print("[SUCCESS] Deployment completed!")
        
        # Get deployment URL
        print("\n[STEP 5] Getting deployment URL...")
        url_result = run_command("railway status", "Getting deployment status")
        
        if url_result:
            print("\n[SUCCESS] Deployment successful!")
            print("Your server is now running on Railway.")
            print("\nNext steps:")
            print("1. Copy the deployment URL from Railway dashboard")
            print("2. Update .cursorrules with the new URL")
            print("3. Test the deployment:")
            print("   curl https://your-railway-url.com/health")
            print("   curl -X POST https://your-railway-url.com/api/interactive-feedback \\")
            print("     -H 'Content-Type: application/json' \\")
            print("     -d '{\"project_directory\": \"/test\", \"summary\": \"Test feedback\"}'")
        else:
            print("[WARNING] Could not get deployment URL. Check Railway dashboard.")
    else:
        print("[ERROR] Deployment failed. Check the error messages above.")

if __name__ == "__main__":
    main()
