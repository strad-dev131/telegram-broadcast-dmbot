# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Create sessions directory
RUN mkdir -p sessions

# Expose port (if needed for web interface in future)
EXPOSE 8000

# Command to run the bot
CMD ["python", "main.py"]
