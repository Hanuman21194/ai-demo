# Use a slim version of Python for a smaller, faster image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for some AI libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your 3 core files and the entrypoint
# (Docker will automatically ignore files listed in your .dockerignore)
COPY . .

ENV OPENAI_API_KEY=""
ENV gpt_model=""
ENV SYSTEM_PROMPT=""

# Expose the ports for both apps
EXPOSE 8000
EXPOSE 8501

# Make the script executable
RUN chmod +x entrypoint.sh

# Run both apps
CMD ["./entrypoint.sh"]