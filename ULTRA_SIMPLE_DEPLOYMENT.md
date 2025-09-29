# 🚀 Ultra Simple Deployment - GitHub Codespaces

## ⚡ Chỉ 3 bước:

### **1. Start Codespace**
```
Vào: https://github.com/phamdanguyen/interactive-feedback-mcp
Click: "Code" → "Codespaces" → "Create codespace on main"
Chờ: 3 phút
```

### **2. Run Server**
```
Trong Codespace terminal:
uv run fastmcp dev server.py
```

### **3. Get Public URL**
```
Click tab "Ports" 
Copy public URL (dạng: https://xxx-8080.app.github.dev)
```

## 📋 MCP Config cho Cursor:
```json
{
  "mcpServers": {
    "interactive-feedback-mcp": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "YOUR_CODESPACE_URL/mcp",
        "-H", "Content-Type: application/json",
        "-d", "@-"
      ],
      "timeout": 600,
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```

## 🎉 Done!
- ✅ Server chạy trên GitHub
- ✅ Public URL có sẵn
- ✅ MCP config cho Cursor
- ✅ Không cần setup gì

**Chỉ mất 5 phút!**
