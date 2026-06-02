FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn terminatori.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
