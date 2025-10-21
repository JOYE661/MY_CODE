FROM docker.1ms.run/python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .

# 安装Python依赖，确保Streamlit版本为1.28.0
RUN pip install --upgrade pip \
    && pip install streamlit==1.28.0 \
    && pip install -r requirements.txt

# 复制项目文件
COPY . .

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ENABLE_CORS=false

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["python", "-m", "streamlit", "run", "streamlit_app.py"]