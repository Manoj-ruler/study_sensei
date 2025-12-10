FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-root user for slight security improvement
RUN useradd -m coder
USER coder

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
