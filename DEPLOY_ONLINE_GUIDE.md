# 🚀 Deploy Interactive Feedback MCP Server Online

## ✅ Server đã sẵn sàng deploy!

Tất cả code đã được push lên GitHub: `phamdanguyen/interactive-feedback-mcp`

## 🎯 Deploy lên Railway (Khuyến nghị)

### Bước 1: Truy cập Railway
1. Vào https://railway.app
2. **Sign up/Login** với GitHub account
3. **Connect GitHub** repository

### Bước 2: Deploy
1. **Click "Deploy from GitHub repo"**
2. **Chọn**: `phamdanguyen/interactive-feedback-mcp`
3. **Railway sẽ tự động detect Python** và deploy
4. **Chờ deployment hoàn tất** (2-3 phút)

### Bước 3: Lấy URL
1. **Click vào project** sau khi deploy
2. **Copy URL** (dạng: `https://xxx-production.up.railway.app`)
3. **Test URL**: Thêm `/health` vào cuối URL

## 🎯 Deploy lên Render (Alternative)

### Bước 1: Truy cập Render
1. Vào https://render.com
2. **Sign up/Login** với GitHub account

### Bước 2: Tạo Web Service
1. **Click "New +" → "Web Service"**
2. **Connect GitHub repo**: `phamdanguyen/interactive-feedback-mcp`
3. **Configure**:
   - **Name**: `interactive-feedback-mcp`
   - **Build Command**: `pip install fastapi uvicorn`
   - **Start Command**: `python railway_server.py`
   - **Environment**: Python 3
4. **Click "Create Web Service"**

### Bước 3: Lấy URL
1. **Chờ deployment** (5-10 phút)
2. **Copy URL** (dạng: `https://xxx.onrender.com`)
3. **Test URL**: Thêm `/health` vào cuối URL

## 🎯 Cấu hình MCP cho Cursor

Sau khi có URL online, thêm vào Cursor `mcp.json`:

```json
{
  "mcpServers": {
    "interactive-feedback-mcp": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "https://YOUR-DEPLOYED-URL.com/api/interactive-feedback",
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

**Thay `YOUR-DEPLOYED-URL.com` bằng URL thực tế từ Railway/Render**

## 🧪 Test Deployment

Sau khi deploy, test với:

```bash
# Test health endpoint
curl https://your-deployed-url.com/health

# Test interactive feedback
curl -X POST https://your-deployed-url.com/api/interactive-feedback \
  -H "Content-Type: application/json" \
  -d '{"project_directory": "/test", "summary": "Test feedback"}'
```

## 🎯 Lợi ích của Online Deployment

### ✅ Zero-Install cho Clients:
- Không cần cài Python, dependencies
- Chỉ cần cấu hình URL trong Cursor
- Hoạt động trên mọi hệ điều hành

### ✅ Centralized Management:
- Một server cho tất cả clients
- Dễ bảo trì và cập nhật
- Consistent experience

### ✅ High Availability:
- Server luôn online
- Auto-scaling khi cần
- Backup và monitoring

## 🎉 Kết quả

**Sau khi deploy thành công:**
- ✅ **Interactive Feedback MCP Server** chạy online
- ✅ **URL công khai** để tất cả máy tính có thể sử dụng
- ✅ **IT Manager Agent** với mandatory feedback
- ✅ **Zero-install** cho clients
- ✅ **Auto-deployment** từ GitHub

## 🆘 Troubleshooting

### Nếu deployment thất bại:
1. **Check GitHub Actions**: Repo → Actions tab
2. **Check deployment logs**: Railway/Render dashboard
3. **Verify requirements.txt**: Đảm bảo có `fastapi uvicorn`

### Nếu MCP không hoạt động:
1. **Check URL**: Đảm bảo URL đúng
2. **Test endpoints**: Dùng curl để test
3. **Check Cursor logs**: Xem MCP connection logs

## 📋 Checklist

- [ ] Deploy lên Railway/Render
- [ ] Lấy deployment URL
- [ ] Test endpoints với curl
- [ ] Update mcp.json với URL thực tế
- [ ] Copy config vào Cursor
- [ ] Restart Cursor
- [ ] Test với IT Manager Agent

**Chọn platform nào để deploy? Railway hay Render?**
