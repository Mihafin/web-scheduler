FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN python3 -m venv venv
RUN venv/bin/pip install --no-cache-dir -r requirements.txt
ENV PORT=8080
CMD
CMD exec venv/bin/uvicorn app.main:app --host 0.0.0.0 --reload --port $PORT
