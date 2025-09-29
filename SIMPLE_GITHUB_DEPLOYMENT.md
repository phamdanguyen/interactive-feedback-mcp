# GitHub Infrastructure Deployment - Đơn Giản

## 🎯 Mục tiêu: Triển khai Interactive Feedback MCP lên GitHub

### ✅ Đã có sẵn:
- **GitHub Actions workflow** (`.github/workflows/`)
- **GitHub Codespaces config** (`.devcontainer/devcontainer.json`)
- **Code đã push** lên GitHub

## 🚀 Cách triển khai đơn giản nhất:

### **Option 1: GitHub Codespaces (Khuyến nghị)**
```bash
1. Vào: https://github.com/phamdanguyen/interactive-feedback-mcp
2. Click "Code" → "Codespaces" → "Create codespace on main"
3. Chờ 3 phút
4. Chạy: uv run fastmcp dev server.py
5. Lấy public URL từ Ports tab
```

### **Option 2: GitHub Actions (Manual trigger)**
```bash
1. Vào: https://github.com/phamdanguyen/interactive-feedback-mcp/actions
2. Click "Simple Deploy Interactive Feedback MCP"
3. Click "Run workflow"
4. Chờ deployment hoàn thành
```

### **Option 3: Local với ngrok**
```bash
1. Chạy: uv run fastmcp dev server.py
2. Chạy: ngrok http 8000
3. Copy public URL
4. Tạo MCP config cho Cursor
```

## 📋 MCP Config cho Cursor:

```json
{
  "mcpServers": {
    "interactive-feedback-mcp": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "YOUR_PUBLIC_URL/mcp",
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

## 🎉 Kết quả:
- ✅ **Interactive Feedback MCP** chạy trên GitHub
- ✅ **Public URL** có sẵn
- ✅ **MCP config** cho Cursor
- ✅ **Không cần setup** phức tạp

**Chọn Option 1 (Codespaces) là đơn giản nhất!**
