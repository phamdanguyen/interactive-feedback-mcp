# 💻 GitHub Codespaces Quick Start

## 🚀 Deploy Interactive Feedback MCP trên GitHub Codespaces

### **✅ Advantages:**
- **Free**: 120 hours/month cho personal accounts
- **Cloud development**: Không cần setup local environment
- **Port forwarding**: Tự động tạo public URL
- **Pre-configured**: Python + dependencies sẵn sàng
- **Integrated**: Tích hợp với GitHub ecosystem

## 📋 Quick Start (3 phút)

### **Step 1: Start Codespace**
1. Vào repository: `https://github.com/phamdanguyen/interactive-feedback-mcp`
2. Click **"Code"** → **"Codespaces"** → **"Create codespace on main"**
3. Chờ Codespace khởi động (2-3 phút)

### **Step 2: Start MCP Server**
```bash
# Server sẽ tự động start sau khi Codespace ready
uv run fastmcp dev server.py
```

### **Step 3: Access Public URL**
- Codespace tự động tạo **public URL**
- Click vào **"Ports"** tab
- Copy **public URL** (dạng: `https://xxx-8080.app.github.dev`)

### **Step 4: Generate MCP Config**
```python
# Chạy script này trong Codespace
import json

public_url = "https://YOUR_CODESPACE_URL"  # Replace với URL thực

mcp_config = {
    "mcpServers": {
        "interactive-feedback-mcp-codespaces": {
            "command": "curl",
            "args": [
                "-X", "POST",
                f"{public_url}/mcp",
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
```

## 🎯 Features

### **✅ Pre-configured Environment:**
- **Python 3.11** với all dependencies
- **FastMCP** và Interactive Feedback MCP
- **Port forwarding** tự động
- **Git integration** sẵn sàng

### **✅ Development Features:**
- **VS Code** trong browser
- **Terminal** access
- **File explorer** 
- **Git integration**
- **Extensions** pre-installed

### **✅ Public Access:**
- **Public URL** tự động tạo
- **HTTPS** enabled
- **No ngrok** required
- **Persistent** trong session

## 🔄 Workflow

### **Development Workflow:**
1. **Start Codespace** từ GitHub
2. **Edit code** trong VS Code
3. **Test changes** với live server
4. **Commit & push** changes
5. **Share public URL** với team

### **Deployment Workflow:**
1. **Push to main** branch
2. **GitHub Actions** auto-deploy
3. **Public URL** available
4. **MCP config** generated
5. **Ready for Cursor** integration

## 💰 Cost Optimization

### **Free Tier Limits:**
- **120 hours/month** cho personal accounts
- **60 hours/month** cho organization accounts
- **Auto-suspend** sau 30 phút inactive

### **Usage Tips:**
- **Stop Codespace** khi không dùng
- **Use scheduled workflows** cho regular deployment
- **Combine với GitHub Actions** cho 24/7 uptime
- **Monitor usage** trong GitHub settings

## 🆚 Comparison với Other Options

| **Platform** | **Cost** | **Setup Time** | **Uptime** | **Features** |
|--------------|----------|----------------|------------|--------------|
| **Railway** | $5/month | 10 phút | 24/7 | Complex setup |
| **Render** | $7/month | 15 phút | 24/7 | Complex setup |
| **Colab** | Free | 5 phút | Session-based | Limited |
| **Codespaces** | **FREE** | **2 phút** | **120h/month** | **Full IDE** |

## 🎉 Perfect Use Cases

### **✅ Development:**
- **Feature development** với live testing
- **Debugging** với full environment
- **Collaboration** với team members
- **Code review** với live demo

### **✅ Testing:**
- **Integration testing** với real environment
- **User acceptance testing** với public URL
- **Performance testing** với cloud resources
- **Cross-platform testing**

### **✅ Demo & Presentation:**
- **Live demo** với public URL
- **Client presentation** với working prototype
- **Team training** với shared environment
- **Documentation** với live examples

## 🚀 Next Steps

1. **✅ Start Codespace** (done)
2. **🔄 Test MCP server** (pending)
3. **📝 Share public URL** (pending)
4. **⚙️ Configure Cursor** (pending)
5. **🎯 Start development** (pending)

## 💡 Pro Tips

### **Maximize Productivity:**
- **Bookmark** Codespace URL
- **Use VS Code extensions** trong browser
- **Enable auto-save** để không mất code
- **Commit frequently** để backup changes

### **Optimize Performance:**
- **Use smaller Codespace** cho simple tasks
- **Close unused ports** để save resources
- **Monitor usage** trong GitHub settings
- **Combine với GitHub Actions** cho production

**🚀 Với GitHub Codespaces, bạn có thể develop và deploy Interactive Feedback MCP Server trong 3 phút mà không cần setup gì cả!**
