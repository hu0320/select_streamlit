# 使用一个官方的 Python 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件到工作目录中
# 这是为了利用Docker的缓存机制，只有当requirements.txt改变时才会重新安装依赖
COPY requirements.txt ./requirements.txt

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将项目中的所有文件复制到工作目录中
# 这包括你的 app.py, .xlsx, 和 .otf 字体文件
COPY . .

# 暴露 Streamlit 默认运行的端口
EXPOSE 8501

# 设置健康检查，告诉Hugging Face如何检查app是否正常运行
HEALTHCHECK CMD streamlit hello --server.port 8501

# 容器启动时要执行的命令
# 启动 Streamlit 应用，并确保它能被外部访问
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]