# Simple Python 3.11 image for Heroku/Koyeb
FROM python:3.11-slim

# Working directory
WORKDIR /app

# Install ffmpeg for yt-dlp
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code
COPY . .

# Create downloads folder
RUN mkdir -p downloads

# Expose port
EXPOSE 1489

# Simple run command
CMD ["uvicorn", "Erixter:app", "--host", "0.0.0.0", "--port", "1489"]
