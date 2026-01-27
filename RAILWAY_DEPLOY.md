# 🚀 Deploy lên Railway

## Bước 1: Chuẩn bị Git Repository

```bash
cd /Users/mac/Royal/customApi

# Khởi tạo git nếu chưa có
git init

# Add tất cả files
git add .

# Commit
git commit -m "Initial commit - NetSuite Proxy API"
```

## Bước 2: Push lên GitHub

```bash
# Tạo repo mới trên GitHub: https://github.com/new
# Tên repo: netsuite-proxy-api

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/netsuite-proxy-api.git

# Push code
git branch -M main
git push -u origin main
```

## Bước 3: Deploy trên Railway

1. **Truy cập Railway**: https://railway.app
2. **Login với GitHub**
3. **New Project** → **Deploy from GitHub repo**
4. **Chọn repo**: `netsuite-proxy-api`
5. Railway sẽ tự động detect và deploy!

## Bước 4: Set Environment Variables

Trong Railway dashboard → **Variables** tab, thêm:

```
ENVIRONMENT=production
PORT=8000
API_KEY=netsuite_proxy_api_key_2026_secure

NETSUITE_REALM=9692499
NETSUITE_CONSUMER_KEY=<your_consumer_key>
NETSUITE_CONSUMER_SECRET=<your_consumer_secret>
NETSUITE_TOKEN_KEY=<your_token_key>
NETSUITE_TOKEN_SECRET=<your_token_secret>

RATE_LIMIT_MAX=100
LOG_LEVEL=info
```

**Lưu ý:** Copy giá trị từ file `.env` của bạn!

## Bước 5: Generate Domain

1. Trong Railway dashboard → **Settings** tab
2. **Generate Domain** → Railway sẽ tạo URL public
3. Hoặc custom domain: **Add Custom Domain**

## Bước 6: Test API

```bash
# Health check
curl https://your-app.railway.app/health

# Test với API key
curl -H "X-API-Key: netsuite_proxy_api_key_2026_secure" \
  "https://your-app.railway.app/api/netsuite/customer?limit=2"
```

## 🎯 URL mẫu cho Airbyte

Sau khi deploy, URL của bạn sẽ là:

- `https://your-app-name.railway.app`

Dùng URL này trong Airbyte HTTP Source:

- **URL**: `https://your-app-name.railway.app/api/netsuite/customer`
- **Headers**: `X-API-Key: netsuite_proxy_api_key_2026_secure`

## 📊 Monitoring

Railway tự động cung cấp:

- **Logs**: Real-time application logs
- **Metrics**: CPU, Memory, Network usage
- **Deploy history**: Rollback nếu cần

## 💰 Chi phí

- **Free tier**: $5 credit/month
- **Pro plan**: $20/month unlimited usage
- API này dùng rất ít resource → Free tier đủ cho testing!

## 🔄 Auto Deploy

Mỗi lần push code lên GitHub, Railway tự động:

1. Pull code mới
2. Build lại
3. Deploy
4. Zero downtime!

## ⚡ Alternative: Deploy ngay không cần GitHub

```bash
# Cài Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy từ folder hiện tại
cd /Users/mac/Royal/customApi
railway init
railway up
```

Xong! 🎉
