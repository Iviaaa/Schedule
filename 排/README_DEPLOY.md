# 部署指南

## 方案一：Render.com（推荐，免费且简单）

### 步骤：

1. **注册账号**
   - 访问 https://render.com
   - 使用 GitHub 账号登录（推荐）或邮箱注册

2. **准备代码**
   ```bash
   # 确保代码已提交到GitHub
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <你的GitHub仓库地址>
   git push -u origin main
   ```

3. **在Render上部署**
   - 登录 Render 后，点击 "New +" → "Web Service"
   - 连接你的 GitHub 仓库
   - 配置如下：
     - **Name**: 排程计算工具（或你喜欢的名字）
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
     - **Plan**: Free（免费计划）
   - 点击 "Create Web Service"

4. **等待部署完成**
   - Render 会自动构建和部署
   - 完成后会给你一个 URL，例如：`https://your-app.onrender.com`

### 注意事项：
- 免费计划在15分钟无活动后会休眠，首次访问需要几秒唤醒
- 每月有750小时免费额度
- 文件上传限制：100MB

---

## 方案二：Railway.app（推荐，简单快速）

### 步骤：

1. **注册账号**
   - 访问 https://railway.app
   - 使用 GitHub 账号登录

2. **部署**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的仓库
   - Railway 会自动检测 Python 项目并部署

3. **配置环境变量（如果需要）**
   - 在项目设置中可以添加环境变量
   - 通常不需要额外配置

4. **获取URL**
   - 部署完成后，Railway 会提供一个公共 URL

### 注意事项：
- 免费计划每月有 $5 额度
- 支持自动部署
- 文件上传限制取决于计划

---

## 方案三：PythonAnywhere（适合初学者）

### 步骤：

1. **注册账号**
   - 访问 https://www.pythonanywhere.com
   - 注册免费账号

2. **上传代码**
   - 在 Files 标签页上传你的代码
   - 或使用 Git 克隆仓库

3. **安装依赖**
   - 在 Bash 控制台运行：
   ```bash
   pip3.10 install --user -r requirements.txt
   ```

4. **配置Web应用**
   - 在 Web 标签页创建新的 Web App
   - 选择 Flask 和 Python 3.10
   - 编辑 WSGI 文件，指向你的 app.py

### 注意事项：
- 免费计划有限制（CPU时间、文件大小等）
- 适合学习和测试

---

## 方案四：使用VPS服务器（需要服务器）

### 步骤：

1. **购买VPS**
   - 推荐：DigitalOcean, Vultr, 阿里云等
   - 选择 Ubuntu 20.04 或更高版本

2. **服务器配置**
   ```bash
   # 更新系统
   sudo apt update && sudo apt upgrade -y
   
   # 安装Python和pip
   sudo apt install python3 python3-pip python3-venv nginx -y
   
   # 克隆代码
   git clone <你的仓库地址>
   cd 排
   
   # 创建虚拟环境
   python3 -m venv venv
   source venv/bin/activate
   
   # 安装依赖
   pip install -r requirements.txt
   
   # 安装gunicorn
   pip install gunicorn
   ```

3. **使用Gunicorn运行**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

4. **配置Nginx反向代理**
   ```bash
   sudo nano /etc/nginx/sites-available/your-app
   ```
   
   添加配置：
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
   
   ```bash
   sudo ln -s /etc/nginx/sites-available/your-app /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **使用systemd管理服务**
   ```bash
   sudo nano /etc/systemd/system/your-app.service
   ```
   
   添加：
   ```ini
   [Unit]
   Description=排程计算工具
   After=network.target
   
   [Service]
   User=your-username
   WorkingDirectory=/path/to/your/app
   Environment="PATH=/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   ```bash
   sudo systemctl enable your-app
   sudo systemctl start your-app
   ```

---

## 方案五：Docker部署（适合容器化）

### 创建 Dockerfile：

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads temp

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "4"]
```

### 部署到Docker平台：
- **Fly.io**: `flyctl launch`
- **Railway**: 自动检测Dockerfile
- **Heroku**: 支持Docker容器

---

## 推荐方案

**对于快速部署**：使用 **Render.com** 或 **Railway.app**
- 免费
- 简单
- 自动部署
- 无需服务器管理

**对于生产环境**：使用 **VPS + Nginx + Gunicorn**
- 完全控制
- 性能更好
- 适合长期使用

---

## 部署后检查清单

- [ ] 应用可以正常访问
- [ ] 文件上传功能正常
- [ ] 计算功能正常
- [ ] 文件下载功能正常
- [ ] 错误处理正常
- [ ] 临时文件自动清理

---

## 常见问题

**Q: 部署后无法访问？**
A: 检查防火墙设置，确保端口开放

**Q: 文件上传失败？**
A: 检查 uploads 和 temp 文件夹权限，确保可写

**Q: 内存不足？**
A: 减少 Gunicorn workers 数量（-w 2 或 -w 1）

**Q: 如何查看日志？**
A: 在 Render/Railway 的控制台可以查看日志

