FROM python:3.10-slim

WORKDIR /app

# Install basic system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# --- NEW FIX: Python-based line ending correction ---
# This replaces dos2unix. It removes Windows \r characters from the script.
RUN python3 -c "import os; content = open('entrypoint.sh', 'rb').read().replace(b'\r\n', b'\n'); open('entrypoint.sh', 'wb').write(content)"
RUN chmod +x entrypoint.sh

# Environment variables (Best practice: pass these at runtime, not in Dockerfile)
ENV OPENAI_API_KEY="placeholder"
ENV gpt_model="gpt-4o"
ENV SYSTEM_PROMPT="You are a helpful assistant."

EXPOSE 8000
EXPOSE 8501

# Use /bin/bash explicitly to execute the script
CMD ["/bin/bash", "./entrypoint.sh"]