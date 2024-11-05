FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    gcc \
    g++ \
    libhdf5-dev \
    libhdf5-serial-dev \
    hdf5-tools \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN pip install --upgrade pip

# 复制并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY api.py .

# 创建输出目录
RUN mkdir -p /app/output

EXPOSE 8008

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8008"]