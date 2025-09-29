# Test deployment and create ngrok tunnel (no emoji version)
import requests
import time
from pyngrok import ngrok

def test_local_server():
    """Test local server"""
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        if response.status_code == 200:
            print("OK: Local server is running")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"ERROR: Local server returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Cannot connect to local server: {e}")
        return False

def create_ngrok_tunnel():
    """Create ngrok tunnel"""
    try:
        print("Creating ngrok tunnel...")
        public_url = ngrok.connect(8000)
        print(f"SUCCESS: Public URL: {public_url}")
        return str(public_url)
    except Exception as e:
        print(f"ERROR: Error creating ngrok tunnel: {e}")
        return None

def test_public_url(public_url):
    """Test public URL"""
    try:
        response = requests.get(public_url, timeout=10)
        if response.status_code == 200:
            print("OK: Public URL is accessible")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"ERROR: Public URL returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Cannot access public URL: {e}")
        return False

def generate_mcp_config(public_url):
    """Generate MCP configuration for Cursor"""
    mcp_config = {
        "mcpServers": {
            "interactive-feedback-mcp-local": {
                "command": "curl",
                "args": [
                    "-X", "POST",
                    f"{public_url}/mcp",
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
    
    print("\nMCP Configuration for Cursor:")
    print("=" * 60)
    import json
    print(json.dumps(mcp_config, indent=2))
    print("=" * 60)
    
    # Save to file
    with open("mcp_config_local.json", "w") as f:
        json.dump(mcp_config, f, indent=2)
    print("Configuration saved to mcp_config_local.json")
    
    return mcp_config

def main():
    print("Testing Interactive Feedback MCP Deployment")
    print("=" * 50)
    
    # Step 1: Test local server
    print("\n1. Testing local server...")
    if not test_local_server():
        print("ERROR: Local server test failed. Make sure server is running:")
        print("   uv run fastmcp dev server.py")
        return
    
    # Step 2: Create ngrok tunnel
    print("\n2. Creating ngrok tunnel...")
    public_url = create_ngrok_tunnel()
    if not public_url:
        print("ERROR: Failed to create ngrok tunnel")
        return
    
    # Step 3: Test public URL
    print("\n3. Testing public URL...")
    time.sleep(2)  # Wait for tunnel to be ready
    if not test_public_url(public_url):
        print("ERROR: Public URL test failed")
        return
    
    # Step 4: Generate MCP config
    print("\n4. Generating MCP configuration...")
    generate_mcp_config(public_url)
    
    print("\nSUCCESS: Deployment test completed successfully!")
    print(f"Public URL: {public_url}")
    print("Copy the MCP configuration above to your Cursor mcp.json")
    print("Restart Cursor to load the new MCP server")

if __name__ == "__main__":
    main()
