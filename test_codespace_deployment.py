# Test deployment trong Codespace
import subprocess
import time
import requests
import threading

def install_dependencies():
    """Install dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.run(["pip", "install", "fastapi", "uvicorn", "fastmcp"], check=True)
        print("✅ Dependencies installed")
        return True
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def test_server_import():
    """Test if server can be imported"""
    print("Testing server import...")
    try:
        import server
        print("✅ Server imports successfully")
        return True
    except Exception as e:
        print(f"❌ Server import failed: {e}")
        return False

def run_server():
    """Run server in background"""
    print("Starting server...")
    try:
        # Try uvicorn first
        subprocess.run([
            "python", "-m", "uvicorn", 
            "server:app", 
            "--host", "0.0.0.0", 
            "--port", "8080"
        ], check=True)
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        return False

def test_server():
    """Test server"""
    print("Testing server...")
    time.sleep(3)  # Wait for server to start
    
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Server returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def main():
    print("Testing Codespace Deployment")
    print("=" * 40)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        return
    
    # Step 2: Test server import
    if not test_server_import():
        return
    
    # Step 3: Run server
    print("\nStarting server...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Step 4: Test server
    if test_server():
        print("\n🎉 SUCCESS! Server is running")
        print("🌐 Public URL: https://jubilant-rotary-phone-q4vjvvjwvwfrx7.github.dev/")
        print("📋 MCP Config for Cursor:")
        print("""
{
  "mcpServers": {
    "interactive-feedback-mcp": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "https://jubilant-rotary-phone-q4vjvvjwvwfrx7.github.dev/mcp",
        "-H", "Content-Type: application/json",
        "-d", "@-"
      ],
      "timeout": 600,
      "autoApprove": ["interactive_feedback"]
    }
  }
}
        """)
    else:
        print("\n❌ Server test failed")

if __name__ == "__main__":
    main()
