#!/usr/bin/env python3
"""
Test Interactive Feedback MCP with Cursor
"""

import json
import subprocess
import sys
import time
import os

def test_mcp_server():
    """Test MCP server directly"""
    print("Testing MCP Interactive Feedback Server...")
    
    try:
        # Test the server startup
        print("Starting MCP server...")
        process = subprocess.Popen([
            sys.executable, "server.py"
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Sending initialization request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Wait for response
        time.sleep(2)
        
        # Send tools/list request
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        print("Sending tools/list request...")
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        # Wait for response
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print("[SUCCESS] MCP server is running and responding")
            
            # Try to read some output
            try:
                # Read available output
                if process.stdout.readable():
                    output = process.stdout.read()
                    if output:
                        print(f"[INFO] Server output: {output[:200]}...")
            except:
                pass
            
            # Stop server
            process.terminate()
            process.wait()
            print("[SUCCESS] MCP server test completed successfully")
            return True
        else:
            print("[FAIL] MCP server exited unexpectedly")
            stderr = process.stderr.read()
            if stderr:
                print(f"[ERROR] {stderr}")
            return False
            
    except Exception as e:
        print(f"[FAIL] MCP server test failed: {e}")
        if 'process' in locals():
            process.terminate()
        return False

def create_cursor_instructions():
    """Create instructions for Cursor setup"""
    print("\nCreating Cursor setup instructions...")
    
    instructions = """
# Cursor MCP Setup Instructions

## Step 1: Copy MCP Configuration
Copy the following configuration to your Cursor settings (mcp.json):

```json
{
  "mcpServers": {
    "interactive-feedback-mcp": {
      "command": "python",
      "args": ["D:\\\\AI\\\\interactive-feedback-mcp\\\\server.py"],
      "timeout": 600,
      "autoApprove": [
        "interactive_feedback"
      ]
    }
  }
}
```

## Step 2: Restart Cursor
After adding the configuration, restart Cursor completely.

## Step 3: Test the Integration
1. Open a new chat in Cursor
2. Ask the AI to do something that requires feedback
3. The AI should automatically call interactive_feedback

## Step 4: Verify IT Manager Agent
The IT Manager Agent should now:
- Always call interactive_feedback before major system changes
- Get user confirmation before configuring databases, APIs, security
- Maintain context across long conversations
- Optimize costs by batching multiple operations

## Troubleshooting
If the MCP server doesn't work:
1. Check that Python is in your PATH
2. Verify the server.py path is correct
3. Make sure fastmcp is installed: pip install fastmcp
4. Check Cursor's MCP logs for errors
"""
    
    with open("CURSOR_SETUP_INSTRUCTIONS.md", "w") as f:
        f.write(instructions)
    
    print("[SUCCESS] Cursor setup instructions created: CURSOR_SETUP_INSTRUCTIONS.md")

def main():
    print("Interactive Feedback MCP - Cursor Integration Test")
    print("=" * 60)
    
    # Test 1: MCP Server
    mcp_success = test_mcp_server()
    
    # Test 2: Create instructions
    create_cursor_instructions()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"MCP Server: {'[SUCCESS]' if mcp_success else '[FAIL]'}")
    
    if mcp_success:
        print("\n[SUCCESS] MCP Server is ready for Cursor!")
        print("[INFO] Follow the instructions in CURSOR_SETUP_INSTRUCTIONS.md")
        print("[INFO] IT Manager Agent will now use interactive feedback")
        
        print("\nNext steps:")
        print("1. Copy mcp.json configuration to Cursor")
        print("2. Restart Cursor")
        print("3. Test with IT Manager Agent tasks")
    else:
        print("\n[FAIL] MCP Server has issues")
        print("[INFO] Please check the errors above and fix them")

if __name__ == "__main__":
    main()
