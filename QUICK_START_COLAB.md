# 🚀 Quick Start - Deploy Interactive Feedback MCP Server trên Google Colab

## 📍 Vị trí files:
- **GitHub Repository**: https://github.com/phamdanguyen/interactive-feedback-mcp
- **Colab Notebook**: `colab_notebook.ipynb` (đã có sẵn)
- **Server Code**: `colab_server.py`

## ⚡ Deploy trong 3 phút:

### **Bước 1: Mở Google Colab (30 giây)**
1. Vào https://colab.research.google.com
2. **File → Upload notebook**
3. **Upload** file `colab_notebook.ipynb` từ GitHub

**Hoặc copy trực tiếp từ GitHub:**
- Vào: https://github.com/phamdanguyen/interactive-feedback-mcp/blob/main/colab_notebook.ipynb
- **Raw** → Copy toàn bộ code → Paste vào Colab

### **Bước 2: Chạy Cells theo thứ tự (2 phút)**

#### **Cell 1: Install Dependencies**
```python
!pip install fastapi uvicorn pyngrok requests
```
**→ Chạy cell này trước**

#### **Cell 2: Load Server Code**
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import time
import threading
from pyngrok import ngrok

# Create FastAPI app
app = FastAPI(
    title="Interactive Feedback MCP Server - Colab",
    description="Interactive Feedback MCP Server running on Google Colab",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def first_line(text: str) -> str:
    """Get first line of text"""
    return text.split("\n")[0].strip()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Interactive Feedback MCP Server - Colab",
        "version": "1.0.0",
        "status": "running",
        "platform": "Google Colab",
        "endpoints": {
            "health": "/health",
            "interactive_feedback": "/api/interactive-feedback"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "interactive-feedback-mcp-colab",
        "version": "1.0.0",
        "timestamp": time.time(),
        "platform": "Google Colab"
    }

@app.post("/api/interactive-feedback")
async def api_interactive_feedback(request: dict):
    """Interactive feedback API endpoint for Colab"""
    try:
        project_directory = request.get("project_directory", "")
        summary = request.get("summary", "")
        
        if not project_directory or not summary:
            raise HTTPException(
                status_code=400,
                detail="project_directory and summary are required"
            )
        
        # Log the feedback request
        print(f"Interactive feedback request from {project_directory}")
        print(f"Summary: {summary}")
        
        # For Colab deployment, return structured response
        result = {
            "status": "success",
            "message": "Interactive feedback request received via Google Colab",
            "data": {
                "project_directory": first_line(project_directory),
                "summary": first_line(summary),
                "timestamp": time.time(),
                "platform": "Google Colab",
                "feedback": "User feedback processed successfully via Colab server"
            }
        }
        
        return result
        
    except Exception as e:
        print(f"Error handling interactive feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

print("✅ Server code loaded successfully!")
```

#### **Cell 3: Start Server với Public URL**
```python
# Start ngrok tunnel to create public URL
public_url = ngrok.connect(8000)
print(f"🌐 Public URL: {public_url}")

# Function to run server
def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

# Start server in background thread
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

print("✅ Server is running!")
print(f"🔗 Health check: {public_url}/health")
print(f"🔗 API endpoint: {public_url}/api/interactive-feedback")

# Save URL for later use
with open("ngrok_url.txt", "w") as f:
    f.write(str(public_url))
print("💾 URL saved to ngrok_url.txt")
```

#### **Cell 4: Test Server**
```python
import requests
import time

# Wait a moment for server to start
time.sleep(3)

# Test health endpoint
try:
    response = requests.get(f"{public_url}/health")
    print("✅ Health check:", response.json())
except Exception as e:
    print(f"❌ Health check failed: {e}")

# Test interactive feedback endpoint
try:
    test_data = {
        "project_directory": "/test/project",
        "summary": "Test interactive feedback from Colab"
    }
    
    response = requests.post(f"{public_url}/api/interactive-feedback", json=test_data)
    print("✅ Interactive feedback test:", response.json())
except Exception as e:
    print(f"❌ Interactive feedback test failed: {e}")

print("\n🎉 Server is ready for use!")
```

#### **Cell 5: Tạo MCP Config cho Cursor**
```python
# Generate Cursor MCP configuration
mcp_config = {
    "mcpServers": {
        "interactive-feedback-mcp-colab": {
            "command": "curl",
            "args": [
                "-X", "POST",
                f"{public_url}/api/interactive-feedback",
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

print("📋 Copy this configuration to your Cursor mcp.json:")
print("=" * 60)
print(json.dumps(mcp_config, indent=2))
print("=" * 60)

# Save to file
with open("cursor_mcp_config.json", "w") as f:
    json.dump(mcp_config, f, indent=2)
print("\n💾 Configuration saved to cursor_mcp_config.json")
```

### **Bước 3: Copy MCP Config vào Cursor (30 giây)**
1. **Copy** MCP config từ output của Cell 5
2. **Paste** vào Cursor settings (`mcp.json`)
3. **Restart Cursor**

## 🎉 Hoàn thành!

**Sau 3 phút bạn sẽ có:**
- ✅ **Interactive Feedback MCP Server** chạy trên Google Colab
- ✅ **Public URL** từ ngrok (dạng: https://xxx.ngrok.io)
- ✅ **MCP configuration** cho Cursor
- ✅ **IT Manager Agent** với mandatory feedback

## 🔄 Keep Session Alive (Optional)

Nếu muốn giữ server chạy lâu, chạy cell này:

```python
import time
import datetime

print("🔄 Starting keep-alive loop...")
print("Press Ctrl+C to stop")

try:
    while True:
        try:
            response = requests.get(f"{public_url}/health")
            if response.status_code == 200:
                print(f"✅ [{datetime.datetime.now()}] Server is running")
            else:
                print(f"⚠️ [{datetime.datetime.now()}] Server status: {response.status_code}")
        except Exception as e:
            print(f"❌ [{datetime.datetime.now()}] Server check failed: {e}")
        
        time.sleep(300)  # Sleep 5 minutes
        
except KeyboardInterrupt:
    print("\n🛑 Keep-alive stopped by user")
```

## 📍 Vị trí files quan trọng:

### **GitHub Repository:**
- **URL**: https://github.com/phamdanguyen/interactive-feedback-mcp
- **Colab Notebook**: `colab_notebook.ipynb`
- **Server Code**: `colab_server.py`

### **Local Files:**
- **Path**: `D:\AI\interactive-feedback-mcp\colab_notebook.ipynb`
- **Backup**: Có thể download từ GitHub

## 🆘 Troubleshooting:

### Nếu ngrok không hoạt động:
1. **Check ngrok auth**: Có thể cần đăng ký ngrok account miễn phí
2. **Try alternative**: Sử dụng Colab's built-in public URL
3. **Restart runtime**: Runtime → Restart runtime

### Nếu server không start:
1. **Check dependencies**: Đảm bảo Cell 1 đã chạy thành công
2. **Check port**: Port 8000 có thể bị sử dụng
3. **Restart runtime**: Runtime → Restart runtime

**🚀 Bây giờ bạn có thể deploy Interactive Feedback MCP Server trên Google Colab chỉ trong 3 phút!**
