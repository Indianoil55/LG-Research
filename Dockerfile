# Python base image
FROM python:3.9-slim

# Working directory set karein
WORKDIR /app

# Files copy karein
COPY . /app

# Dependencies install karein
RUN pip install --no-cache-dir -r requirements.txt

# Port expose karein
EXPOSE 8000

# Start command
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
