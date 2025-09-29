# 🚀 Deploy Interactive Feedback MCP Server trên Google Colab

## ✅ Hoàn toàn khả thi!

Google Colab có thể chạy FastAPI server và expose public URL thông qua ngrok hoặc Colab's built-in features.

## 🎯 Cách deploy trên Google Colab

### Bước 1: Tạo Colab Notebook
1. Vào https://colab.research.google.com
2. **Tạo notebook mới**
3. **Upload** file `colab_server.py` vào Colab

### Bước 2: Install Dependencies
```python
# Cell 1: Install dependencies
!pip install fastapi uvicorn pyngrok
```

### Bước 3: Setup ngrok (Tạo public URL)
```python
# Cell 2: Setup ngrok
from pyngrok import ngrok
import uvicorn
import threading
from colab_server import app

# Start ngrok tunnel
public_url = ngrok.connect(8000)
print(f"Public URL: {public_url}")
```

### Bước 4: Chạy Server
```python
# Cell 3: Run server
def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Start server in background thread
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

print("Server is running!")
print(f"Health check: {public_url}/health")
print(f"API endpoint: {public_url}/api/interactive-feedback")
```

### Bước 5: Test Server
```python
# Cell 4: Test server
import requests

# Test health endpoint
response = requests.get(f"{public_url}/health")
print("Health check:", response.json())

# Test interactive feedback
test_data = {
    "project_directory": "/test/project",
    "summary": "Test from Colab"
}

response = requests.post(f"{public_url}/api/interactive-feedback", json=test_data)
print("Interactive feedback test:", response.json())
```

## 🎯 Lợi ích của Google Colab

### ✅ Hoàn toàn miễn phí:
- Không cần đăng ký thêm service
- Sử dụng Google account có sẵn
- Không giới hạn thời gian (với free tier)

### ✅ Dễ setup:
- Chỉ cần copy-paste code
- Không cần cài đặt gì trên máy
- Chạy trực tiếp trên browser

### ✅ Public URL tự động:
- ngrok tạo public URL miễn phí
- Có thể access từ bất kỳ đâu
- HTTPS tự động

### ✅ Persistent:
- Colab session có thể chạy lâu
- Code được save tự động
- Có thể restart và chạy lại

## 🎯 Cấu hình MCP cho Cursor

Sau khi có public URL từ Colab, thêm vào Cursor `mcp.json`:

```json
{
  "mcpServers": {
    "interactive-feedback-mcp-colab": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "https://YOUR-COLAB-NGROK-URL.ngrok.io/api/interactive-feedback",
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
```

**Thay `YOUR-COLAB-NGROK-URL.ngrok.io` bằng URL thực tế từ Colab**

## 🧪 Test Deployment

```python
# Test trong Colab
import requests

# Test health
response = requests.get("https://your-url.ngrok.io/health")
print(response.json())

# Test interactive feedback
data = {"project_directory": "/test", "summary": "Test from Colab"}
response = requests.post("https://your-url.ngrok.io/api/interactive-feedback", json=data)
print(response.json())
```

## 🔄 Restart Colab Session

Nếu Colab session bị timeout:
1. **Restart runtime**: Runtime → Restart runtime
2. **Chạy lại các cells** theo thứ tự
3. **Lấy URL mới** từ ngrok (URL có thể thay đổi)
4. **Update mcp.json** với URL mới

## 💡 Tips cho Colab

### ✅ Keep Session Alive:
```python
# Chạy cell này để keep session alive
import time
while True:
    time.sleep(300)  # Sleep 5 minutes
    print("Session alive...")
```

### ✅ Save ngrok URL:
```python
# Lưu URL để dùng sau
with open("ngrok_url.txt", "w") as f:
    f.write(str(public_url))
```

### ✅ Monitor Server:
```python
# Check server status
import requests
try:
    response = requests.get(f"{public_url}/health")
    print("Server is running:", response.json())
except:
    print("Server is down, restart needed")
```

## 🎉 Kết quả

**Với Google Colab:**
- ✅ **Hoàn toàn miễn phí**
- ✅ **Setup trong 5 phút**
- ✅ **Public URL tự động**
- ✅ **Chạy 100% Python**
- ✅ **Zero-install cho clients**
- ✅ **IT Manager Agent ready**

## 🆘 Troubleshooting

### Nếu ngrok không hoạt động:
1. **Check ngrok auth**: Có thể cần đăng ký ngrok account
2. **Try alternative**: Sử dụng Colab's built-in public URL
3. **Check firewall**: Đảm bảo port 8000 không bị block

### Nếu server không start:
1. **Check dependencies**: Đảm bảo đã install đủ packages
2. **Check port**: Port 8000 có thể bị sử dụng
3. **Restart runtime**: Runtime → Restart runtime

**Google Colab là giải pháp hoàn hảo cho việc này! Bạn có muốn tôi tạo Colab notebook hoàn chỉnh không?**
