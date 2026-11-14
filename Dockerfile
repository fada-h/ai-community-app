# 青禾 · AI 校园社区 —— 单镜像部署（前端 dist + FastAPI 同源）
# 构建：docker build -t qinghe .
# 运行：docker run -p 8000:8000 -e DEEPSEEK_API_KEY=sk-xxx qinghe
# 访问：http://localhost:8000

# ---------- 1. 构建前端 ----------
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---------- 2. 运行后端并托管前端 ----------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRONTEND_DIST=/frontend/dist

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=web /web/dist /frontend/dist

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
