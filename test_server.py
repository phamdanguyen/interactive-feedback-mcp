#!/usr/bin/env python3
"""
Test Interactive Feedback MCP Server
"""

import requests
import json
import time
import subprocess
import sys

def test_server():
    """Test the server functionality"""
    print("Testing Interactive Feedback MCP Server...")
    
    # Test data
    test_data = {
        "project_directory": "/test/project",
        "summary": "Test interactive feedback request"
    }
    
    try:
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test interactive feedback endpoint
        print("\n2. Testing interactive feedback endpoint...")
        response = requests.post(
            "http://localhost:8000/api/interactive-feedback",
            json=test_data,
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Interactive feedback endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Interactive feedback endpoint failed: {response.status_code}")
            return False
        
        print("\n✅ All tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Please start the server first:")
        print("   python railway_server.py")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def start_server_and_test():
    """Start server and test it"""
    print("Starting server and running tests...")
    
    # Start server in background
    server_process = subprocess.Popen([
        sys.executable, "railway_server.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    # Test server
    success = test_server()
    
    # Stop server
    server_process.terminate()
    server_process.wait()
    
    return success

if __name__ == "__main__":
    print("Interactive Feedback MCP Server Test")
    print("=" * 50)
    
    # Check if server is already running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("Server is already running. Testing...")
            success = test_server()
        else:
            print("Server not responding properly. Starting new server...")
            success = start_server_and_test()
    except:
        print("Server not running. Starting new server...")
        success = start_server_and_test()
    
    if success:
        print("\n🎉 Server test completed successfully!")
        print("Ready for deployment!")
    else:
        print("\n❌ Server test failed!")
        print("Please check the server code and try again.")
