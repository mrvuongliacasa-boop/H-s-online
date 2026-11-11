# Build từ thư mục lia-casa-10-ty:  docker build -f chatbot/Dockerfile -t liacasa-bot .
FROM python:3.12-slim
WORKDIR /app
COPY chatbot/requirements.txt chatbot/requirements.txt
RUN pip install --no-cache-dir -r chatbot/requirements.txt
COPY chatbot/ chatbot/
COPY landing/catalog.json landing/catalog.json
ENV PORT=8080
EXPOSE 8080
CMD ["python", "-m", "chatbot.server"]
