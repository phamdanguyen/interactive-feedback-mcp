#!/usr/bin/env python3
"""
Test MCP Interactive Feedback locally
"""

import json
import subprocess
import sys
import time
import tempfile
import os

def test_mcp_server():
    """Test the MCP server directly"""
    print("Testing MCP Interactive Feedback Server locally...")
    
    # Test data
    test_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "interactive_feedback",
            "arguments": {
                "project_directory": "/test/project",
                "summary": "Test interactive feedback from MCP"
            }
        }
    }
    
    try:
        # Start MCP server
        print("Starting MCP server...")
        server_process = subprocess.Popen([
            sys.executable, "server.py"
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Send test request
        print("Sending test request...")
        server_process.stdin.write(json.dumps(test_data) + "\n")
        server_process.stdin.flush()
        
        # Wait for response
        time.sleep(2)
        
        # Check if process is still running
        if server_process.poll() is None:
            print("✅ MCP server is running")
            
            # Try to get response
            try:
                server_process.stdin.write(json.dumps({"method": "tools/list"}) + "\n")
                server_process.stdin.flush()
                time.sleep(1)
                
                # Read any available output
                if server_process.stdout.readable():
                    output = server_process.stdout.read()
                    if output:
                        print(f"✅ Server response: {output[:200]}...")
                    else:
                        print("⚠️ No output from server")
                
            except Exception as e:
                print(f"⚠️ Could not read server output: {e}")
            
            # Stop server
            server_process.terminate()
            server_process.wait()
            print("✅ MCP server test completed")
            return True
        else:
            print("❌ MCP server exited unexpectedly")
            stderr = server_process.stderr.read()
            if stderr:
                print(f"Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        if 'server_process' in locals():
            server_process.terminate()
        return False

def test_web_server():
    """Test the web server"""
    print("\nTesting Web Interactive Feedback Server...")
    
    try:
        # Start web server
        print("Starting web server...")
        web_process = subprocess.Popen([
            sys.executable, "railway_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Test with curl
        test_data = {
            "project_directory": "/test/project",
            "summary": "Test web server interactive feedback"
        }
        
        print("Testing web server with curl...")
        curl_process = subprocess.run([
            "curl", "-X", "POST",
            "http://localhost:8000/api/interactive-feedback",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(test_data)
        ], capture_output=True, text=True, timeout=10)
        
        if curl_process.returncode == 0:
            print("✅ Web server test passed")
            print(f"Response: {curl_process.stdout}")
            success = True
        else:
            print("❌ Web server test failed")
            print(f"Error: {curl_process.stderr}")
            success = False
        
        # Stop web server
        web_process.terminate()
        web_process.wait()
        
        return success
        
    except Exception as e:
        print(f"❌ Web server test failed: {e}")
        if 'web_process' in locals():
            web_process.terminate()
        return False

def main():
    print("Interactive Feedback MCP Server Test Suite")
    print("=" * 60)
    
    # Test 1: MCP Server
    mcp_success = test_mcp_server()
    
    # Test 2: Web Server
    web_success = test_web_server()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"MCP Server: {'✅ PASS' if mcp_success else '❌ FAIL'}")
    print(f"Web Server: {'✅ PASS' if web_success else '❌ FAIL'}")
    
    if mcp_success and web_success:
        print("\n🎉 All tests passed! Server is ready for deployment.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    print("\nNext steps:")
    print("1. If tests pass, deploy to Railway/Render")
    print("2. Update mcp.json with deployment URL")
    print("3. Test with Cursor")

if __name__ == "__main__":
    main()
