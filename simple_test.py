#!/usr/bin/env python3
"""
Simple test for Interactive Feedback MCP Server
"""

import subprocess
import sys
import time
import json

def test_server_import():
    """Test if server can be imported"""
    print("Testing server import...")
    try:
        # Test MCP server import
        result = subprocess.run([
            sys.executable, "-c", "from server import mcp; print('MCP server import: OK')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ MCP server import: PASS")
            print(f"   {result.stdout.strip()}")
            mcp_ok = True
        else:
            print("❌ MCP server import: FAIL")
            print(f"   {result.stderr}")
            mcp_ok = False
        
        # Test web server import
        result = subprocess.run([
            sys.executable, "-c", "from railway_server import app; print('Web server import: OK')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Web server import: PASS")
            print(f"   {result.stdout.strip()}")
            web_ok = True
        else:
            print("❌ Web server import: FAIL")
            print(f"   {result.stderr}")
            web_ok = False
        
        return mcp_ok, web_ok
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False, False

def test_mcp_server():
    """Test MCP server startup"""
    print("\nTesting MCP server startup...")
    try:
        # Start server and check if it starts without errors
        process = subprocess.Popen([
            sys.executable, "server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a bit
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ MCP server started successfully")
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            print("❌ MCP server failed to start")
            if stderr:
                print(f"   Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return False

def test_web_server():
    """Test web server startup"""
    print("\nTesting web server startup...")
    try:
        # Start server and check if it starts without errors
        process = subprocess.Popen([
            sys.executable, "railway_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a bit
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Web server started successfully")
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            print("❌ Web server failed to start")
            if stderr:
                print(f"   Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Web server test failed: {e}")
        return False

def create_cursor_config():
    """Create Cursor configuration"""
    print("\nCreating Cursor configuration...")
    
    config = {
        "mcpServers": {
            "interactive-feedback-mcp-local": {
                "command": "python",
                "args": ["server.py"],
                "timeout": 600,
                "autoApprove": ["interactive_feedback"]
            }
        }
    }
    
    # Save to mcp.json
    with open("mcp.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Cursor configuration created: mcp.json")
    print("\nTo use with Cursor:")
    print("1. Copy mcp.json to your Cursor settings")
    print("2. Restart Cursor")
    print("3. The IT Manager Agent will now use interactive feedback")

def main():
    print("Interactive Feedback MCP Server - Simple Test")
    print("=" * 60)
    
    # Test 1: Server imports
    mcp_import, web_import = test_server_import()
    
    # Test 2: Server startup
    mcp_startup = test_mcp_server() if mcp_import else False
    web_startup = test_web_server() if web_import else False
    
    # Test 3: Create Cursor config
    create_cursor_config()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"MCP Server Import: {'✅ PASS' if mcp_import else '❌ FAIL'}")
    print(f"MCP Server Startup: {'✅ PASS' if mcp_startup else '❌ FAIL'}")
    print(f"Web Server Import: {'✅ PASS' if web_import else '❌ FAIL'}")
    print(f"Web Server Startup: {'✅ PASS' if web_startup else '❌ FAIL'}")
    
    if mcp_import and mcp_startup:
        print("\n🎉 MCP Server is ready!")
        print("✅ You can now use it with Cursor")
        print("✅ IT Manager Agent will use interactive feedback")
    else:
        print("\n⚠️ MCP Server has issues. Please check the errors above.")
    
    if web_import and web_startup:
        print("✅ Web server is ready for deployment!")
    else:
        print("⚠️ Web server has issues.")

if __name__ == "__main__":
    main()
