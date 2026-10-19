FROM python:3.12-slim
WORKDIR /app
COPY services/morgenzeitung /app/services/morgenzeitung
COPY Privat/Pressespiegel /app/Privat/Pressespiegel
ENV PAPER_HOST=0.0.0.0 PORT=8765 PAPER_DB=/data/morgenzeitung.sqlite PYTHONUNBUFFERED=1
EXPOSE 8765
CMD ["python", "/app/services/morgenzeitung/start.py"]
