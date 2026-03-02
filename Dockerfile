FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要的套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY webpage_monitor.py .

# 建立資料目錄
RUN mkdir -p /data

# 設定時區為台北時間
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 執行程式
CMD ["python", "webpage_monitor.py"]
