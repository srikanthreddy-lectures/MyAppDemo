FROM python:3.10-slim

# Install system dependencies required for some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory contents to /app
# This will place the 'app' and 'static' folders inside /app
COPY backend/ .

# Hugging Face Spaces requires the app to listen on port 7860
EXPOSE 7860

# Start the FastAPI application using uvicorn
# We refer to 'app.main:app' because the 'app' folder is now in the root /app directory
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
