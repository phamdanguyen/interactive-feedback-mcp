# 🚀 Codespace Deployment Instructions

## ⚡ Chạy trong Codespace:

### **1. Install dependencies:**
```bash
pip install fastapi uvicorn fastmcp
```

### **2. Test server:**
```bash
python test_codespace_deployment.py
```

### **3. Hoặc chạy manual:**
```bash
# Chạy server
python -m uvicorn server:app --host 0.0.0.0 --port 8080

# Test server
curl http://localhost:8080
```

## 📋 MCP Config cho Cursor:
```json
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
```

## 🎯 Steps:
1. ✅ **Codespace**: https://jubilant-rotary-phone-q4vjvvjwvwfrx7.github.dev/
2. 🔄 **Install**: `pip install fastapi uvicorn fastmcp`
3. 🚀 **Run**: `python -m uvicorn server:app --host 0.0.0.0 --port 8080`
4. 📋 **Copy MCP config** vào Cursor
5. 🎉 **Test** với Cursor

**Public URL đã sẵn sàng: https://jubilant-rotary-phone-q4vjvvjwvwfrx7.github.dev/**
