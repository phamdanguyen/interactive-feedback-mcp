# Simple test to trigger GitHub Actions deployment
import requests
import time

def check_github_actions():
    """Check GitHub Actions status"""
    print("Checking GitHub Actions deployment...")
    
    # GitHub Actions API endpoint
    api_url = "https://api.github.com/repos/phamdanguyen/interactive-feedback-mcp/actions/runs"
    
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("workflow_runs"):
                latest_run = data["workflow_runs"][0]
                status = latest_run.get("status", "unknown")
                conclusion = latest_run.get("conclusion", "unknown")
                
                print(f"Latest workflow run:")
                print(f"  Status: {status}")
                print(f"  Conclusion: {conclusion}")
                print(f"  URL: {latest_run.get('html_url', 'N/A')}")
                
                return latest_run
            else:
                print("No workflow runs found")
                return None
        else:
            print(f"API request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error checking GitHub Actions: {e}")
        return None

def main():
    print("GitHub Actions Deployment Test")
    print("=" * 40)
    
    # Check current workflow status
    workflow_run = check_github_actions()
    
    if workflow_run:
        print("\nTo view deployment:")
        print(f"1. Go to: {workflow_run.get('html_url', 'https://github.com/phamdanguyen/interactive-feedback-mcp/actions')}")
        print("2. Look for 'Deploy Interactive Feedback MCP Server' workflow")
        print("3. Check the workflow summary for public URL")
        print("4. Copy MCP configuration from the summary")
    
    print("\nManual trigger:")
    print("1. Go to: https://github.com/phamdanguyen/interactive-feedback-mcp/actions")
    print("2. Click 'Deploy Interactive Feedback MCP Server'")
    print("3. Click 'Run workflow'")
    print("4. Wait for deployment to complete")

if __name__ == "__main__":
    main()
