# Fix Codespace UV Command Not Found

## 🚨 Lỗi: `bash: uv: command not found`

### ✅ Giải pháp:

#### **Option 1: Install uv trong Codespace**
```bash
# Trong Codespace terminal:
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Sau đó chạy:
uv run fastmcp dev server.py
```

#### **Option 2: Dùng pip thay vì uv**
```bash
# Install dependencies:
pip install fastapi uvicorn fastmcp

# Chạy server:
fastmcp dev server.py
```

#### **Option 3: Dùng Python trực tiếp**
```bash
# Install dependencies:
pip install fastapi uvicorn

# Chạy server:
python -m uvicorn server:app --host 0.0.0.0 --port 8080
```

## 🎯 Khuyến nghị:

**Dùng Option 2** (pip) vì đơn giản nhất:

```bash
pip install fastapi uvicorn fastmcp
fastmcp dev server.py
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

## 🎉 Sau khi fix:
1. ✅ Server chạy trên Codespace
2. ✅ Public URL: https://jubilant-rotary-phone-q4vjvvjwvwfrx7.github.dev/
3. ✅ Copy MCP config vào Cursor
4. ✅ Test với Cursor
