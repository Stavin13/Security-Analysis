# Use Python 3.9 image
FROM python:3.9

# Pros:
# - Includes all Python dependencies
# - More system libraries pre-installed
# - Better for complex requirements
# - Includes development tools

# Cons:
# - Much larger size (~900MB)
# - Slower to build and pull
# - Uses more disk space

# Set working directory
WORKDIR /app

# Install system dependencies including curl
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create cache directory for models
RUN mkdir -p /root/.cache/huggingface/

# Pre-download and cache models
RUN python -c "from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification; \
    model_name='nlptown/bert-base-multilingual-uncased-sentiment'; \
    pipeline('text-classification', model=model_name, tokenizer=model_name); \
    AutoTokenizer.from_pretrained('bert-base-uncased'); \
    AutoModelForSequenceClassification.from_pretrained('bert-base-uncased')"

# Download NLTK data
RUN python -c "import nltk; nltk.download('vader_lexicon')"

# Copy the rest of the application
COPY . .

# Create database directory
RUN mkdir -p /app/instance && chmod 777 /app/instance

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Copy the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use an entrypoint script
ENTRYPOINT ["/entrypoint.sh"]