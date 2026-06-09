FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y traceroute inetutils-traceroute && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure data directory exists
RUN mkdir -p data

# Run main using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]