# 使用 Python 3.11 官方镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建数据目录
RUN mkdir -p data/images

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=data/orders.db
ENV IMAGES_DIR=data/images

# 初始化数据库
RUN python database.py

# 暴露端口（如果需要 webhook 模式）
EXPOSE 8080

# 启动命令
CMD ["python", "bot.py"]
